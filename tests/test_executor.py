"""Tests του paper executor με in-memory fakes (χωρίς εξωτερικές υπηρεσίες)."""
from datetime import datetime, timezone

import pytest

from app.execution.executor import PaperExecutor
from app.models.market import Ticker
from app.strategy.mean_reversion import MeanReversionStrategy


class FakePositionStore:
    def __init__(self):
        self._d = {}

    async def set(self, pos):
        self._d[pos.symbol] = pos

    async def get(self, symbol):
        return self._d.get(symbol)

    async def get_all(self):
        return list(self._d.values())

    async def delete(self, symbol):
        self._d.pop(symbol, None)


class FakeTickerCache:
    def __init__(self, prices):
        self._p = dict(prices)

    async def get(self, symbol):
        p = self._p.get(symbol)
        return Ticker(symbol=symbol, price=p, timestamp=datetime.now(timezone.utc)) if p else None

    async def set_latest(self, t):
        self._p[t.symbol] = t.price


class FakeCollector:
    def __init__(self, candles):
        self.candles = candles

    async def fetch_ohlcv(self, symbol, tf, limit):
        return self.candles


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _fake_sessionmaker():
    return _FakeSession()


@pytest.fixture
def captured_trades(monkeypatch):
    trades = []

    async def fake_save_trade(session, trade):
        trades.append(trade)

    monkeypatch.setattr("app.execution.executor.save_trade", fake_save_trade)
    return trades


async def test_buy_then_sell(make_candles, warmup_prices, captured_trades):
    store = FakePositionStore()
    tcache = FakeTickerCache({"BTC/USDT": 90.0})
    strat = MeanReversionStrategy(20, 2.0, 0.0)

    # 1) dip -> BUY
    ex = PaperExecutor(strat, FakeCollector(make_candles(warmup_prices + [90.0])), tcache,
                       store, _fake_sessionmaker, ["BTC/USDT"], "1h",
                       capital_per_symbol=10_000.0, fee_rate=0.001, interval=60)
    await ex.step()
    pos = await store.get("BTC/USDT")
    assert pos is not None and abs(pos.entry_price - 90.0) < 1e-9
    assert captured_trades == []  # καμία κλεισμένη συναλλαγή ακόμα

    # 2) revert up -> SELL
    tcache._p["BTC/USDT"] = 110.0
    ex.collector = FakeCollector(make_candles(warmup_prices + [110.0]))
    await ex.step()
    assert await store.get("BTC/USDT") is None       # θέση έκλεισε
    assert len(captured_trades) == 1
    assert captured_trades[0].pnl > 0                 # κερδοφόρα


async def test_no_double_buy(make_candles, warmup_prices, captured_trades):
    store = FakePositionStore()
    tcache = FakeTickerCache({"BTC/USDT": 90.0})
    ex = PaperExecutor(MeanReversionStrategy(20, 2.0, 0.0),
                       FakeCollector(make_candles(warmup_prices + [90.0])), tcache,
                       store, _fake_sessionmaker, ["BTC/USDT"], "1h", 10_000.0, 0.001, 60)
    await ex.step()
    first = await store.get("BTC/USDT")
    await ex.step()  # ξανά dip, αλλά έχουμε ήδη θέση
    second = await store.get("BTC/USDT")
    assert first.entry_time == second.entry_time  # καμία νέα αγορά
