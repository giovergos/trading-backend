"""Κεντρική διαμόρφωση μέσω μεταβλητών περιβάλλοντος (pydantic-settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "trading-backend"
    environment: str = "development"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "trading"
    postgres_password: str = "trading"
    postgres_db: str = "trading"

    redis_host: str = "redis"
    redis_port: int = 6379

    # --- Αγορά / CEX ---
    exchange_id: str = "binance"
    symbols: str = "BTC/USDT,ETH/USDT"
    timeframe: str = "1h"
    ohlcv_backfill_limit: int = 500
    ws_reconnect_delay: float = 5.0

    # --- On-chain / Ethereum ---
    eth_rpc_url: str = ""
    eth_poll_interval: float = 12.0
    stablecoin_threshold: float = 1_000_000.0
    onchain_max_block_span: int = 50

    # --- Strategy (Φάση 4) ---
    strategy_window: int = 20
    strategy_num_std: float = 2.0
    strategy_exit_z: float = 0.0

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
