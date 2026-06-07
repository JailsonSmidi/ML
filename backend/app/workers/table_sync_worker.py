import logging
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy import select, delete
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models import MLShippingRate, MLCommissionRate, MLTableSyncLog, Notification
from app.services.ml_table_scraper import scrape_shipping_table, scrape_commission_table
from app.services.notification_service import create_notification
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.table_sync_worker.sync_ml_tables")
def sync_ml_tables():
    """
    Roda diariamente via Celery Beat.
    Faz scraping das tabelas públicas do ML, compara com os valores
    salvos no banco e atualiza se houver mudança.
    Notifica via dashboard e email se detectar alterações.
    """
    asyncio.run(_sync_ml_tables_async())


async def _sync_ml_tables_async():
    logger.info("Iniciando sincronização das tabelas do ML...")

    async with AsyncSessionLocal() as db:
        all_changes = []

        # ─── Tabela de fretes ──────────────────────────────────────────────
        try:
            new_shipping_rates = await scrape_shipping_table()
            shipping_changes = await _sync_shipping_rates(db, new_shipping_rates)
            all_changes.extend(shipping_changes)

            await _log_sync(
                db,
                table_name="ml_shipping_rates",
                changes=shipping_changes,
            )
        except Exception as exc:
            logger.error(f"Erro ao sincronizar fretes: {exc}")
            await _log_sync(
                db,
                table_name="ml_shipping_rates",
                changes=[],
                error=str(exc),
            )

        # ─── Tabela de comissões ───────────────────────────────────────────
        try:
            new_commission_rates = await scrape_commission_table()
            commission_changes = await _sync_commission_rates(db, new_commission_rates)
            all_changes.extend(commission_changes)

            await _log_sync(
                db,
                table_name="ml_commission_rates",
                changes=commission_changes,
            )
        except Exception as exc:
            logger.error(f"Erro ao sincronizar comissões: {exc}")
            await _log_sync(
                db,
                table_name="ml_commission_rates",
                changes=[],
                error=str(exc),
            )

        # ─── Notifica se houve mudanças ────────────────────────────────────
        if all_changes:
            logger.info(f"Mudanças detectadas: {len(all_changes)} alterações")
            await create_notification(
                db=db,
                notification_type="table_sync_change",
                title="Tabelas do Mercado Livre atualizadas",
                body=_format_changes_body(all_changes),
                send_email=True,
            )
        else:
            logger.info("Nenhuma mudança detectada nas tabelas do ML.")

        await db.commit()


async def _sync_shipping_rates(db, new_rates: list[dict]) -> list[dict]:
    """Compara e atualiza tabela de fretes. Retorna lista de mudanças."""
    changes = []

    # Busca registros atuais
    result = await db.execute(select(MLShippingRate))
    current_rates = {
        f"{r.logistics}_{r.weight_min_kg}_{r.weight_max_kg}_{r.price_min}_{r.price_max}": r
        for r in result.scalars().all()
    }

    # Limpa e reinsere (mais simples que diff linha a linha para tabelas pequenas)
    await db.execute(delete(MLShippingRate))

    for rate_data in new_rates:
        key = f"{rate_data['logistics']}_{rate_data['weight_min_kg']}_{rate_data['weight_max_kg']}_{rate_data.get('price_min')}_{rate_data.get('price_max')}"
        old = current_rates.get(key)

        if old and float(old.rate) != float(rate_data["rate"]):
            changes.append({
                "table": "fretes",
                "logistics": rate_data["logistics"],
                "weight": f"{rate_data['weight_min_kg']}–{rate_data['weight_max_kg']} kg",
                "old_value": float(old.rate),
                "new_value": float(rate_data["rate"]),
            })

        db.add(MLShippingRate(**rate_data))

    return changes


async def _sync_commission_rates(db, new_rates: list[dict]) -> list[dict]:
    """Compara e atualiza tabela de comissões. Retorna lista de mudanças."""
    changes = []

    result = await db.execute(select(MLCommissionRate))
    current_rates = {
        f"{r.category_id}_{r.ad_type}": r
        for r in result.scalars().all()
    }

    await db.execute(delete(MLCommissionRate))

    for rate_data in new_rates:
        key = f"{rate_data['category_id']}_{rate_data['ad_type']}"
        old = current_rates.get(key)

        if old and float(old.commission_rate) != float(rate_data["commission_rate"]):
            changes.append({
                "table": "comissões",
                "category": rate_data["category_name"],
                "ad_type": rate_data["ad_type"],
                "old_value": float(old.commission_rate),
                "new_value": float(rate_data["commission_rate"]),
            })

        db.add(MLCommissionRate(**rate_data))

    return changes


async def _log_sync(db, table_name: str, changes: list, error: str | None = None):
    log = MLTableSyncLog(
        table_name=table_name,
        changes_detected=len(changes) > 0,
        changes_detail=changes if changes else None,
        synced_at=datetime.now(timezone.utc),
        error_message=error,
    )
    db.add(log)


def _format_changes_body(changes: list[dict]) -> str:
    lines = [f"Foram detectadas {len(changes)} alteração(ões) nas tabelas do Mercado Livre:\n"]
    for c in changes:
        if c["table"] == "fretes":
            lines.append(
                f"• Frete {c['logistics'].upper()} | {c['weight']}: "
                f"R$ {c['old_value']:.2f} → R$ {c['new_value']:.2f}"
            )
        else:
            lines.append(
                f"• Comissão {c['category']} ({c['ad_type']}): "
                f"{c['old_value']:.1f}% → {c['new_value']:.1f}%"
            )
    lines.append("\nRevise os produtos afetados no dashboard.")
    return "\n".join(lines)
