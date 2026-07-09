"""Live cache τελευταίων τιμών στο Redis (hash: σύμβολο -> JSON Ticker)."""
from app.infra import cache
from app.models.market import Ticker

_HASH_KEY = "tickers:latest"


class TickerCache:
    async def set_latest(self, ticker: Ticker) -> None:
        await cache.get_redis().hset(_HASH_KEY, ticker.symbol, ticker.model_dump_json())

    async def get_all(self) -> list[Ticker]:
        data = await cache.get_redis().hgetall(_HASH_KEY)
        return [Ticker.model_validate_json(v) for v in data.values()]

    async def get(self, symbol: str) -> Ticker | None:
        raw = await cache.get_redis().hget(_HASH_KEY, symbol)
        return Ticker.model_validate_json(raw) if raw else None
