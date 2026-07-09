"""Συλλέκτης CEX (Binance): ιστορικά OHLCV (REST) + live tickers (WebSocket)."""
import asyncio
import logging

from app.collectors.exchange import get_exchange
from app.infra.ticker_cache import TickerCache
from app.models.market import Candle, Ticker

log = logging.getLogger(__name__)


class CEXCollector:
    def __init__(self, symbols, timeframe, ticker_cache: TickerCache, reconnect_delay=5.0):
        self.symbols = symbols
        self.timeframe = timeframe
        self.ticker_cache = ticker_cache
        self.reconnect_delay = reconnect_delay

    async def fetch_ohlcv(self, symbol, timeframe, limit) -> list[Candle]:
        rows = await get_exchange().fetch_ohlcv(symbol, timeframe, limit=limit)
        return [Candle.from_ccxt(symbol, timeframe, row) for row in rows]

    async def _watch_symbol(self, symbol) -> None:
        exchange = get_exchange()
        while True:
            try:
                raw = await exchange.watch_ticker(symbol)
                await self.ticker_cache.set_latest(Ticker.from_ccxt(symbol, raw))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("WS σφάλμα %s: %s — reconnect σε %ss", symbol, exc, self.reconnect_delay)
                await asyncio.sleep(self.reconnect_delay)

    async def run(self) -> None:
        await asyncio.gather(*(self._watch_symbol(s) for s in self.symbols))
