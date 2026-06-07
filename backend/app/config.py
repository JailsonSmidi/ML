from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Banco
    database_url: str

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Anthropic
    anthropic_api_key: str

    # Resend
    resend_api_key: str
    notification_email_from: str
    notification_email_to: str

    # Proxy
    proxy_url: str | None = None

    # App
    app_env: str = "development"
    secret_key: str

    # Scheduler
    table_sync_hour: int = 9
    table_sync_minute: int = 0
    batch_interval_minutes: int = 30
    batch_size: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
