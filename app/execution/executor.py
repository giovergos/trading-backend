"""Paper Trading Executor — το live αντίστοιχο του backtester.

Σε κάθε κύκλο, για κάθε σύμβολο:
  1. τραβά τα πιο πρόσφατα κεριά (REST)·
  2. διαβάζει την τρέχουσα θέση από το Redis·
  3. καλεί τον ΙΔΙΟ πυρήνα strategy.evaluate(candles, in_position) — την
     πανομοιότυπη λογική με το backtest·
  4. προσομοιώνει εκτέλεση: BUY ανοίγει long, SELL κλείνει & καταγράφει τη
     συναλλαγή (realized PnL) στην PostgreSQL.

Δεν εκτελούνται πραγματικές συναλλαγές — μόνο προσομοίωση (paper).
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.execution.position_store import PositionStore
from app.infra.paper_trades import save_trade
from app.infra.ticker_cache import TickerCache
from app.models.paper import PaperPosition, PaperTrade
from app.strategy.mean_reversion import MeanReversionStrategy, Signal

log = logging.getLogger(__name__)


class PaperExecutor:
    def __init__(self, strategy: MeanReversionStrategy, collector, ticker_cache: TickerCache,
                 position_store: PositionStore, sessionmaker, symbols: list[str], timeframe: str,
                 capital_per_symbol: float, fee_rate: float, interval: float):
        self.strategy = strategy
        self.collector = collector
        self.ticker_cache = ticker_cache
        self.position_store = position_store
        self.sessionmaker = sessionmaker
        self.symbols = symbols
        self.timeframe = timeframe
        self.capital_per_symbol = capital_per_symbol
        self.fee_rate = fee_rate
        self.interval = interval

    async def _current_price(self, symbol: str, candles) -> float:
        ticker = await self.ticker_cache.get(symbol)
        return ticker.price if ticker else candles[-1].close

    async def step(self) -> None:
        for symbol in self.symbols:
            candles = await self.collector.fetch_ohlcv(symbol, self.timeframe, self.strategy.window + 1)
            position = await self.position_store.get(symbol)
            decision = self.strategy.evaluate(candles, in_position=position is not None)
            price = await self._current_price(symbol, candles)

            if decision.signal is Signal.BUY and position is None:
                units = self.capital_per_symbol * (1 - self.fee_rate) / price
                await self.position_store.set(PaperPosition(
                    symbol=symbol, units=units, entry_price=price,
                    entry_time=datetime.now(timezone.utc),
                ))
                log.info("PAPER BUY %s: %.6f @ %.2f", symbol, units, price)

            elif decision.signal is Signal.SELL and position is not None:
                proceeds = position.units * price * (1 - self.fee_rate)
                cost = position.units * position.entry_price
                pnl = proceeds - cost
                trade = PaperTrade(
                    symbol=symbol, entry_time=position.entry_time, entry_price=position.entry_price,
                    exit_time=datetime.now(timezone.utc), exit_price=price,
                    pnl=pnl, return_pct=(pnl / cost * 100) if cost else 0.0,
                )
                async with self.sessionmaker() as session:
                    await save_trade(session, trade)
                await self.position_store.delete(symbol)
                log.info("PAPER SELL %s @ %.2f | pnl=%.2f", symbol, price, pnl)

    async def run(self) -> None:
        while True:
            try:
                await self.step()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("Paper executor σφάλμα: %s", exc)
            await asyncio.sleep(self.interval)
