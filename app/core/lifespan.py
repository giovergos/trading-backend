"""Lifespan: αρχικοποίηση/καθαρισμός πόρων & background tasks.

Startup:  ανοίγει Postgres, Redis, exchange client· ξεκινά το background task
          που τραβά live τιμές μέσω WebSocket.
Shutdown: ακυρώνει το task και κλείνει καθαρά όλες τις συνδέσεις.
"""
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.collectors import exchange
from app.collectors.cex import CEXCollector
from app.config import get_settings
from app.infra import cache, database

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # --- πόροι ---
    database.init_engine()
    cache.init_redis()
    exchange.init_exchange()

    # --- collector + live ροή σε background ---
    collector = CEXCollector(
        symbols=settings.symbol_list,
        timeframe=settings.timeframe,
        reconnect_delay=settings.ws_reconnect_delay,
    )
    app.state.collector = collector
    stream_task = asyncio.create_task(collector.run())
    log.info("Live streaming ξεκίνησε για: %s", settings.symbol_list)

    yield

    # --- shutdown ---
    stream_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await stream_task
    await exchange.close_exchange()
    await cache.close_redis()
    await database.dispose_engine()
