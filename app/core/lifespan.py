"""Lifespan: αρχικοποίηση/καθαρισμός πόρων & background tasks."""
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.collectors import exchange, web3_client
from app.collectors.cex import CEXCollector
from app.collectors.onchain import MAINNET_STABLECOINS, OnChainCollector
from app.config import Settings, get_settings
from app.infra import cache, candles as candles_repo, database
from app.infra.onchain_cache import GasCache
from app.infra.ticker_cache import TickerCache
from app.strategy.mean_reversion import MeanReversionStrategy

log = logging.getLogger(__name__)


async def _startup_backfill(collector: CEXCollector, settings: Settings) -> None:
    sessionmaker = database.get_sessionmaker()
    for symbol in settings.symbol_list:
        try:
            fetched = await collector.fetch_ohlcv(symbol, settings.timeframe, settings.ohlcv_backfill_limit)
            async with sessionmaker() as session:
                stored = await candles_repo.save_candles(session, fetched)
            log.info("Backfill %s: αποθηκεύτηκαν %d κεριά", symbol, stored)
        except Exception as exc:
            log.warning("Backfill απέτυχε για %s: %s", symbol, exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    tasks: list[asyncio.Task] = []

    database.init_engine()
    cache.init_redis()
    exchange.init_exchange()
    web3_client.init_web3()
    try:
        await database.create_all()
    except Exception as exc:
        log.warning("Δημιουργία πινάκων απέτυχε: %s", exc)

    # CEX
    ticker_cache = TickerCache()
    collector = CEXCollector(settings.symbol_list, settings.timeframe, ticker_cache, settings.ws_reconnect_delay)
    app.state.collector = collector
    app.state.ticker_cache = ticker_cache
    tasks.append(asyncio.create_task(collector.run()))
    tasks.append(asyncio.create_task(_startup_backfill(collector, settings)))

    # On-chain (προαιρετικό)
    gas_cache = GasCache()
    app.state.gas_cache = gas_cache
    if web3_client.is_enabled():
        onchain = OnChainCollector(
            gas_cache, database.get_sessionmaker(), MAINNET_STABLECOINS,
            settings.stablecoin_threshold, settings.eth_poll_interval, settings.onchain_max_block_span,
        )
        tasks.append(asyncio.create_task(onchain.run()))
        log.info("On-chain συλλογή ενεργή.")

    # Strategy (καθαρός πυρήνας, κοινός για API/backtest/executor)
    app.state.strategy = MeanReversionStrategy(
        window=settings.strategy_window,
        num_std=settings.strategy_num_std,
        exit_z=settings.strategy_exit_z,
    )

    log.info("Startup ολοκληρώθηκε. Σύμβολα: %s", settings.symbol_list)
    yield

    for task in tasks:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await web3_client.close_web3()
    await exchange.close_exchange()
    await cache.close_redis()
    await database.dispose_engine()
