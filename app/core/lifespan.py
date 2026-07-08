"""Lifespan: αρχικοποίηση/καθαρισμός πόρων & background tasks.

Startup:  Postgres (+ δημιουργία πινάκων), Redis, exchange client· ξεκινά
          (α) το live WebSocket streaming και (β) ένα αρχικό backfill ιστορικών.
Shutdown: ακυρώνει τα tasks και κλείνει καθαρά όλες τις συνδέσεις.
"""
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.collectors import exchange
from app.collectors.cex import CEXCollector
from app.config import Settings, get_settings
from app.infra import cache, candles as candles_repo, database
from app.infra.ticker_cache import TickerCache

log = logging.getLogger(__name__)


async def _startup_backfill(collector: CEXCollector, settings: Settings) -> None:
    """Αρχικό γέμισμα ιστορικών κεριών στη βάση (idempotent, μη μπλοκάρον)."""
    sessionmaker = database.get_sessionmaker()
    for symbol in settings.symbol_list:
        try:
            fetched = await collector.fetch_ohlcv(
                symbol, settings.timeframe, settings.ohlcv_backfill_limit
            )
            async with sessionmaker() as session:
                stored = await candles_repo.save_candles(session, fetched)
            log.info("Backfill %s: αποθηκεύτηκαν %d κεριά", symbol, stored)
        except Exception as exc:
            log.warning("Backfill απέτυχε για %s: %s", symbol, exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # --- πόροι ---
    database.init_engine()
    cache.init_redis()
    exchange.init_exchange()
    try:
        await database.create_all()
    except Exception as exc:
        log.warning("Δημιουργία πινάκων απέτυχε (η βάση ίσως δεν είναι έτοιμη): %s", exc)

    # --- collector: live ροή -> Redis, ιστορικά -> Postgres ---
    ticker_cache = TickerCache()
    collector = CEXCollector(
        symbols=settings.symbol_list,
        timeframe=settings.timeframe,
        ticker_cache=ticker_cache,
        reconnect_delay=settings.ws_reconnect_delay,
    )
    app.state.collector = collector
    app.state.ticker_cache = ticker_cache

    stream_task = asyncio.create_task(collector.run())
    backfill_task = asyncio.create_task(_startup_backfill(collector, settings))
    log.info("Live streaming + backfill ξεκίνησαν για: %s", settings.symbol_list)

    yield

    # --- shutdown ---
    for task in (stream_task, backfill_task):
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await exchange.close_exchange()
    await cache.close_redis()
    await database.dispose_engine()
