"""Tests μετατροπών domain μοντέλων."""
from app.models.market import Candle, Ticker


def test_candle_from_ccxt():
    c = Candle.from_ccxt("BTC/USDT", "1h", [1_700_000_000_000, 100, 105, 95, 102, 10])
    assert c.symbol == "BTC/USDT" and c.timeframe == "1h"
    assert (c.open, c.high, c.low, c.close, c.volume) == (100, 105, 95, 102, 10)
    assert c.timestamp.year == 2023 and c.timestamp.tzinfo is not None


def test_ticker_from_ccxt():
    t = Ticker.from_ccxt("ETH/USDT", {"last": 3000.5, "timestamp": 1_700_000_000_000})
    assert t.symbol == "ETH/USDT" and t.price == 3000.5


def test_ticker_missing_timestamp():
    t = Ticker.from_ccxt("ETH/USDT", {"last": 3000.5})
    assert t.price == 3000.5  # δεν σκάει χωρίς timestamp
