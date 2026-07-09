"""Live αποθήκη ανοιχτών paper θέσεων στο Redis (hash: σύμβολο -> JSON)."""
from app.infra import cache
from app.models.paper import PaperPosition

_KEY = "paper:positions"


class PositionStore:
    async def set(self, position: PaperPosition) -> None:
        await cache.get_redis().hset(_KEY, position.symbol, position.model_dump_json())

    async def get(self, symbol: str) -> PaperPosition | None:
        raw = await cache.get_redis().hget(_KEY, symbol)
        return PaperPosition.model_validate_json(raw) if raw else None

    async def get_all(self) -> list[PaperPosition]:
        data = await cache.get_redis().hgetall(_KEY)
        return [PaperPosition.model_validate_json(v) for v in data.values()]

    async def delete(self, symbol: str) -> None:
        await cache.get_redis().hdel(_KEY, symbol)
