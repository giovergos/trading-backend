"""Endpoints κατάστασης συστήματος."""
from fastapi import APIRouter

from app.infra import cache, database

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    db_ok = await database.ping()
    redis_ok = await cache.ping()
    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {"status": status, "dependencies": {"postgres": db_ok, "redis": redis_ok}}
