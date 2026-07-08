"""Κεντρική διαμόρφωση μέσω μεταβλητών περιβάλλοντος (pydantic-settings)."""
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

    # --- Αγορά / CEX (Φάση 1) ---
    exchange_id: str = "binance"
    # Κρατάμε τα σύμβολα ως string χωρισμένο με κόμμα: αποφεύγει το gotcha
    # του pydantic-settings που απαιτεί JSON για λίστες μέσα από .env.
    symbols: str = "BTC/USDT,ETH/USDT"
    timeframe: str = "1h"
    ohlcv_backfill_limit: int = 500
    ws_reconnect_delay: float = 5.0  # δευτ. αναμονής πριν το reconnect

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def symbol_list(self) -> list[str]:
        return [s.strip() for s in self.symbols.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
