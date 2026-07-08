"""Συλλέκτης δεδομένων CEX (Binance μέσω ccxt).

Δύο ρόλοι:
  * fetch_ohlcv(): ιστορικά κεριά μέσω REST — η βάση για το backtesting.
  * run(): live ροή τιμών μέσω WebSocket, με ένα task ανά σύμβολο και
    αυτόματο reconnect σε σφάλμα δικτύου (ανθεκτικότητα real-time).

Στη Φάση 1 η live κατάσταση κρατιέται σε μνήμη (LatestPriceStore). Στη Φάση 2
θα μεταφερθεί σε Redis (live cache) και τα ιστορικά σε PostgreSQL.
"""
import asyncio
import logging

from app.collectors.exchange import get_exchange
from app.models.market import Candle, Ticker

log = logging.getLogger(__name__)


class LatestPriceStore:
    """Προσωρινή in-memory αποθήκη τελευταίων τιμών (Φάση 1)."""

    def __init__(self) -> None:
        self._data: dict[str, Ticker] = {}

    def update(self, ticker: Ticker) -> None:
        self._data[ticker.symbol] = ticker

    def all(self) -> list[Ticker]:
        return list(self._data.values())

    def get(self, symbol: str) -> Ticker | None:
        return self._data.get(symbol)


class CEXCollector:
    def __init__(self, symbols: list[str], timeframe: str, reconnect_delay: float = 5.0) -> None:
        self.symbols = symbols
        self.timeframe = timeframe
        self.reconnect_delay = reconnect_delay
        self.store = LatestPriceStore()

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        """Ιστορικά OHLCV μέσω REST -> λίστα από typed Candle."""
        exchange = get_exchange()
        rows = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [Candle.from_ccxt(symbol, timeframe, row) for row in rows]

    async def _watch_symbol(self, symbol: str) -> None:
        """Ατέρμονο loop: παρακολουθεί live ticker ενός συμβόλου."""
        exchange = get_exchange()
        while True:
            try:
                raw = await exchange.watch_ticker(symbol)
                self.store.update(Ticker.from_ccxt(symbol, raw))
            except asyncio.CancelledError:
                raise  # κανονικός τερματισμός στο shutdown
            except Exception as exc:
                log.warning("WS σφάλμα για %s: %s — reconnect σε %ss",
                            symbol, exc, self.reconnect_delay)
                await asyncio.sleep(self.reconnect_delay)

    async def run(self) -> None:
        """Τρέχει παράλληλα ένα watch loop ανά σύμβολο."""
        await asyncio.gather(*(self._watch_symbol(s) for s in self.symbols))
