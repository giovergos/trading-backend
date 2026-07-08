"""Κεντρική διαμόρφωση μέσω μεταβλητών περιβάλλοντος.

Χρησιμοποιούμε pydantic-settings ώστε όλες οι ρυθμίσεις (βάση, cache, κλειδιά)
να διαβάζονται από .env / environment με validation τύπων. Έτσι η ίδια εικόνα
Docker τρέχει σε διαφορετικά περιβάλλοντα χωρίς αλλαγή κώδικα.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "trading-backend"
    environment: str = "development"

    # PostgreSQL
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "trading"
    postgres_password: str = "trading"
    postgres_db: str = "trading"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    """Singleton ρυθμίσεων (διαβάζονται μία φορά ανά process)."""
    return Settings()
