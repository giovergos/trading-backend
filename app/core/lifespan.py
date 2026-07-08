"""Lifespan της εφαρμογής: αρχικοποίηση & καθαρισμός πόρων.

Εδώ ανοίγουν οι συνδέσεις σε Postgres/Redis στο startup και κλείνουν στο
shutdown. Σε επόμενες φάσεις θα ξεκινούν εδώ και τα background asyncio tasks
(collectors, executor).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infra import cache, database


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_engine()
    cache.init_redis()
    # Φάση 1+: εδώ θα ξεκινούν τα background tasks (π.χ. WebSocket collector)
    yield
    await cache.close_redis()
    await database.dispose_engine()
