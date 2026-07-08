"""Live cache τελευταίων τιμών στο Redis (αντικαθιστά το in-memory store).

Αποθηκεύουμε τα tickers ως πεδία ενός Redis hash: field = σύμβολο,
value = JSON του Ticker. Έτσι το API διαβάζει την τρέχουσα κατάσταση από το
Redis χωρίς να αγγίζει την PostgreSQL.
"""
from app.infra import cache
from app.models.market import Ticker

_HASH_KEY = "tickers:latest"


class TickerCache:
    async def set_latest(self, ticker: Ticker) -> None:
        redis = cache.get_redis()
        await redis.hset(_HASH_KEY, ticker.symbol, ticker.model_dump_json())

    async def get_all(self) -> list[Ticker]:
        redis = cache.get_redis()
        data = await redis.hgetall(_HASH_KEY)
        return [Ticker.model_validate_json(v) for v in data.values()]

    async def get(self, symbol: str) -> Ticker | None:
        redis = cache.get_redis()
        raw = await redis.hget(_HASH_KEY, symbol)
        return Ticker.model_validate_json(raw) if raw else None
