"""Συλλέκτης δεδομένων CEX (Binance μέσω ccxt).

  * fetch_ohlcv(): ιστορικά κεριά μέσω REST -> typed Candle (για persistence/backtest).
  * run(): live ροή τιμών μέσω WebSocket, ένα task ανά σύμβολο, με αυτόματο
    reconnect σε σφάλμα δικτύου. Κάθε ενημέρωση γράφεται στο Redis (TickerCache).

Ο collector παραμένει αποσυνδεδεμένος από την υλοποίηση αποθήκευσης: δέχεται
ένα ticker_cache αντικείμενο και δεν ξέρει ότι από πίσω είναι Redis.
"""
import asyncio
import logging

from app.collectors.exchange import get_exchange
from app.infra.ticker_cache import TickerCache
from app.models.market import Candle, Ticker

log = logging.getLogger(__name__)


class CEXCollector:
    def __init__(
        self,
        symbols: list[str],
        timeframe: str,
        ticker_cache: TickerCache,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.symbols = symbols
        self.timeframe = timeframe
        self.ticker_cache = ticker_cache
        self.reconnect_delay = reconnect_delay

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        exchange = get_exchange()
        rows = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [Candle.from_ccxt(symbol, timeframe, row) for row in rows]

    async def _watch_symbol(self, symbol: str) -> None:
        exchange = get_exchange()
        while True:
            try:
                raw = await exchange.watch_ticker(symbol)
                await self.ticker_cache.set_latest(Ticker.from_ccxt(symbol, raw))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("WS σφάλμα για %s: %s — reconnect σε %ss",
                            symbol, exc, self.reconnect_delay)
                await asyncio.sleep(self.reconnect_delay)

    async def run(self) -> None:
        await asyncio.gather(*(self._watch_symbol(s) for s in self.symbols))
