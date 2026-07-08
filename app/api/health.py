"""Endpoints κατάστασης συστήματος.

Το /health επιστρέφει τη συνδεσιμότητα με τις εξαρτήσεις (Postgres, Redis).
Χρησιμεύει (α) στο Docker healthcheck και (β) στην αξιολόγηση του Κεφ. 5
ως απόδειξη ορθής λειτουργίας του API.
"""
from fastapi import APIRouter

from app.infra import cache, database

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    db_ok = await database.ping()
    redis_ok = await cache.ping()
    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "dependencies": {"postgres": db_ok, "redis": redis_ok},
    }
