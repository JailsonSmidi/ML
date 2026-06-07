from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "ml_research",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.pdf_worker",
        "app.workers.scraper_worker",
        "app.workers.table_sync_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Rate limiting do scraper — máx 1 tarefa de scraping por vez
    task_routes={
        "app.workers.scraper_worker.run_scraper_batch": {
            "queue": "scraper",
            "rate_limit": "2/m",
        },
        "app.workers.pdf_worker.process_pdf": {
            "queue": "pdf",
        },
        "app.workers.table_sync_worker.sync_ml_tables": {
            "queue": "sync",
        },
    },

    beat_schedule={
        # Sincronização diária das tabelas do ML
        "sync-ml-tables-daily": {
            "task": "app.workers.table_sync_worker.sync_ml_tables",
            "schedule": crontab(
                hour=settings.table_sync_hour,
                minute=settings.table_sync_minute,
            ),
        },

        # Scheduler de lotes — verifica a cada 5 min se há lote pronto para processar
        # O worker decide internamente se já passaram 30 min desde o último lote
        "dispatch-next-batch": {
            "task": "app.workers.scraper_worker.dispatch_next_batch",
            "schedule": 300.0,  # a cada 5 minutos
        },
    },
)
