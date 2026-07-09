"""Κοινά fixtures για τη σουίτα tests.

Τα tests είναι σχεδιασμένα να τρέχουν ΧΩΡΙΣ εξωτερικές υπηρεσίες (Binance,
Ethereum, PostgreSQL, Redis): ο καθαρός πυρήνας δεν τις χρειάζεται, και για τα
υπόλοιπα χρησιμοποιούμε in-memory fakes.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.market import Candle
from app.strategy.mean_reversion import MeanReversionStrategy


@pytest.fixture
def make_candles():
    def _make(prices, symbol="BTC/USDT", timeframe="1h"):
        t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        return [
            Candle(symbol=symbol, timeframe=timeframe, timestamp=t0 + timedelta(hours=i),
                   open=p, high=p, low=p, close=p, volume=1.0)
            for i, p in enumerate(prices)
        ]
    return _make


@pytest.fixture
def strategy():
    return MeanReversionStrategy(window=20, num_std=2.0, exit_z=0.0)


@pytest.fixture
def warmup_prices():
    """20 κεριά με διακύμανση (std=1) γύρω από το 100."""
    return [99.0 if i % 2 == 0 else 101.0 for i in range(20)]
