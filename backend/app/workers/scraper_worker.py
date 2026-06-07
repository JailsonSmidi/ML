import logging
from datetime import datetime, timezone, timedelta
from celery import shared_task
from sqlalchemy import select, and_
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models import Product, Batch, Listing
from app.services.scraper import scrape_listings
from app.services.visit_estimator import estimate_visits
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.scraper_worker.dispatch_next_batch")
def dispatch_next_batch():
    """
    Roda a cada 5 minutos via Celery Beat.
    Verifica se há lote 'queued' elegível para processamento
    (respeita o intervalo mínimo de 30 min entre lotes).
    Não bloqueia em lotes 'awaiting_selection' — segue para o próximo.
    """
    asyncio.run(_dispatch_next_batch_async())


async def _dispatch_next_batch_async():
    async with AsyncSessionLocal() as db:
        # Verifica se algum lote está em processamento agora
        processing = await db.execute(
            select(Batch).where(Batch.status == "processing").limit(1)
        )
        if processing.scalar_one_or_none():
            logger.info("Lote já em processamento, aguardando...")
            return

        # Verifica o intervalo desde o último lote que saiu de 'processing'
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=settings.batch_interval_minutes
        )
        last_finished = await db.execute(
            select(Batch)
            .where(Batch.status.in_(["awaiting_selection", "done", "error"]))
            .order_by(Batch.finished_at.desc())
            .limit(1)
        )
        last = last_finished.scalar_one_or_none()

        if last and last.finished_at and last.finished_at > cutoff:
            remaining = (last.finished_at + timedelta(minutes=settings.batch_interval_minutes) - datetime.now(timezone.utc))
            logger.info(f"Aguardando intervalo. Próximo lote em {int(remaining.total_seconds() / 60)} min.")
            return

        # Busca o próximo lote na fila (menor batch_number ainda queued)
        next_batch_result = await db.execute(
            select(Batch)
            .where(Batch.status == "queued")
            .order_by(Batch.batch_number.asc())
            .limit(1)
        )
        next_batch = next_batch_result.scalar_one_or_none()

        if not next_batch:
            logger.info("Nenhum lote na fila.")
            return

        logger.info(f"Despachando lote {next_batch.batch_number} (id: {next_batch.id})")
        next_batch.status = "processing"
        next_batch.started_at = datetime.now(timezone.utc)
        await db.commit()

        # Dispara o task de scraping para esse lote
        run_scraper_batch.apply_async(
            args=[str(next_batch.id)],
            queue="scraper",
        )


@celery_app.task(
    name="app.workers.scraper_worker.run_scraper_batch",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def run_scraper_batch(self, batch_id: str):
    """
    Processa um lote completo: para cada produto do lote,
    faz scraping dos anúncios no ML e calcula métricas estimadas.
    Ao terminar, marca o lote como 'awaiting_selection' e segue.
    """
    asyncio.run(_run_scraper_batch_async(self, batch_id))


async def _run_scraper_batch_async(task, batch_id: str):
    async with AsyncSessionLocal() as db:
        batch = await db.get(Batch, batch_id)
        if not batch:
            logger.error(f"Lote {batch_id} não encontrado")
            return

        # Busca produtos do lote
        result = await db.execute(
            select(Product).where(
                and_(Product.batch_id == batch_id, Product.status == "pending")
            )
        )
        products = result.scalars().all()
        logger.info(f"[Lote {batch.batch_number}] {len(products)} produtos para scraping")

        for product in products:
            try:
                product.status = "scraping"
                await db.commit()

                logger.info(
                    f"[Lote {batch.batch_number}] Scraping: {product.catalog_name} "
                    f"| termo: {product.best_search_term}"
                )

                # Coleta anúncios do ML
                raw_listings = await scrape_listings(
                    search_term=product.best_search_term,
                    proxy_url=settings.proxy_url,
                )

                # Processa e salva cada anúncio
                listings_to_save = []
                for raw in raw_listings:
                    visits_est = estimate_visits(
                        search_position=raw.get("search_position", 999),
                        sales_tag=raw.get("sales_tag", 0),
                        listing_age_days=raw.get("listing_age_days", 1),
                    )

                    # Filtro mínimo de visitação estimada
                    if visits_est < 100:
                        continue

                    sales_per_day = (
                        raw["sales_tag"] / max(raw.get("listing_age_days", 1), 1)
                        if raw.get("sales_tag")
                        else None
                    )

                    listing = Listing(
                        product_id=product.id,
                        ml_item_id=raw["ml_item_id"],
                        title=raw["title"],
                        price=raw["price"],
                        thumbnail_url=raw.get("thumbnail_url"),
                        listing_type=raw.get("listing_type", "organic"),
                        logistics=raw.get("logistics", "mercado_envios"),
                        ad_type=raw.get("ad_type", "classic"),
                        sales_tag=raw.get("sales_tag"),
                        listing_age_days=raw.get("listing_age_days"),
                        search_position=raw.get("search_position"),
                        estimated_visits_7d=visits_est,
                        sales_per_day_est=sales_per_day,
                    )
                    listings_to_save.append(listing)

                db.add_all(listings_to_save)
                product.status = "awaiting_selection"
                await db.commit()

                logger.info(
                    f"[Lote {batch.batch_number}] {product.catalog_name}: "
                    f"{len(listings_to_save)} anúncios salvos"
                )

            except Exception as exc:
                logger.error(
                    f"[Lote {batch.batch_number}] Erro em {product.catalog_name}: {exc}"
                )
                product.status = "error"
                product.error_message = str(exc)
                await db.commit()

        # Marca lote como aguardando seleção — NÃO bloqueia próximo lote
        batch.status = "awaiting_selection"
        batch.finished_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            f"[Lote {batch.batch_number}] Concluído → awaiting_selection. "
            "Próximo lote será despachado pelo scheduler."
        )
