import base64
import logging
from celery import shared_task
from sqlalchemy.orm import Session as DBSession
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models import Product, Batch, Session
from app.services.pdf_parser import parse_catalog_pdf
from app.services.term_validator import validate_search_terms
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.pdf_worker.process_pdf",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def process_pdf(self, session_id: str, pdf_bytes_b64: str):
    """
    Recebe o PDF em base64, extrai todos os produtos via Claude Vision,
    gera termos de busca e salva no banco. Não faz scraping — apenas prepara
    os produtos para os lotes do scraper_worker.
    """
    asyncio.run(_process_pdf_async(self, session_id, pdf_bytes_b64))


async def _process_pdf_async(task, session_id: str, pdf_bytes_b64: str):
    pdf_bytes = base64.b64decode(pdf_bytes_b64)

    async with AsyncSessionLocal() as db:
        try:
            # Atualiza status da sessão
            session = await db.get(Session, session_id)
            if not session:
                logger.error(f"Sessão {session_id} não encontrada")
                return

            session.status = "processing"
            await db.commit()

            # 1. Extrai produtos do PDF via Claude Vision
            logger.info(f"[{session_id}] Iniciando extração do PDF...")
            extracted_products = await parse_catalog_pdf(pdf_bytes)
            logger.info(f"[{session_id}] {len(extracted_products)} produtos extraídos")

            # 2. Para cada produto, valida e seleciona o melhor termo de busca
            products_to_save = []
            for idx, item in enumerate(extracted_products):
                logger.info(
                    f"[{session_id}] Validando termos do produto {idx + 1}/{len(extracted_products)}: {item['catalog_name']}"
                )

                best_term, all_terms = await validate_search_terms(
                    item["catalog_name"],
                    item.get("description", ""),
                    item.get("search_terms_candidates", []),
                )

                product = Product(
                    session_id=session_id,
                    catalog_name=item["catalog_name"],
                    description=item.get("description"),
                    cost_price=item["cost_price"],
                    units_per_box=item.get("units_per_box"),
                    weight_kg=item.get("weight_kg"),
                    dimensions_cm=item.get("dimensions_cm"),
                    search_terms=all_terms,
                    best_search_term=best_term,
                    status="pending",
                )
                products_to_save.append(product)

            # 3. Salva todos os produtos e cria os lotes
            db.add_all(products_to_save)
            await db.flush()

            # Divide em lotes de BATCH_SIZE e cria registros de Batch
            batch_size = settings.batch_size
            for batch_num, start in enumerate(
                range(0, len(products_to_save), batch_size), start=1
            ):
                batch_products = products_to_save[start : start + batch_size]
                batch = Batch(
                    session_id=session_id,
                    batch_number=batch_num,
                    status="queued",
                )
                db.add(batch)
                await db.flush()

                for product in batch_products:
                    product.batch_id = batch.id
                    product.batch_number = batch_num

            session.status = "awaiting_review"
            await db.commit()

            logger.info(
                f"[{session_id}] PDF processado. "
                f"{len(products_to_save)} produtos em "
                f"{(len(products_to_save) + batch_size - 1) // batch_size} lotes."
            )

        except Exception as exc:
            logger.error(f"[{session_id}] Erro no processamento do PDF: {exc}")
            if session:
                session.status = "error"
                await db.commit()
            raise task.retry(exc=exc)
