from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "fundit-service"
    service_port: int = 8500
    environment: str = "dev"

    postgres_dsn: str = "postgresql+psycopg://fundit:fundit@postgres:5432/fundit"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"

    stripe_api_url: str = "https://api.stripe.com"
    yoomoney_api_url: str = "https://yoomoney.ru"

    jwt_secret: str = "fundit-dev-secret"
    encryption_key: str = "fundit-dev-encryption-key"

    project_page_load_target_seconds: float = 2.0
    payment_throughput_target_per_minute: int = 1000
    concurrent_users_target: int = 10000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
