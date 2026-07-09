"""Redis cache για το πιο πρόσφατο on-chain snapshot (gas/block)."""
from app.infra import cache
from app.models.onchain import GasSnapshot

_KEY = "onchain:gas"


class GasCache:
    async def set(self, snapshot: GasSnapshot) -> None:
        await cache.get_redis().set(_KEY, snapshot.model_dump_json())

    async def get(self) -> GasSnapshot | None:
        raw = await cache.get_redis().get(_KEY)
        return GasSnapshot.model_validate_json(raw) if raw else None
