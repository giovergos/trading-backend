"""Tests του καθαρού πυρήνα στρατηγικής (mean reversion)."""
from app.strategy.mean_reversion import Signal


def test_warmup_returns_hold(strategy, make_candles):
    d = strategy.evaluate(make_candles([100.0] * 5))
    assert d.signal is Signal.HOLD and d.mean is None


def test_entry_on_lower_band(strategy, make_candles, warmup_prices):
    d = strategy.evaluate(make_candles(warmup_prices + [90.0]), in_position=False)
    assert d.signal is Signal.BUY
    assert d.price <= d.lower and d.z_score < 0


def test_no_entry_within_bands(strategy, make_candles, warmup_prices):
    d = strategy.evaluate(make_candles(warmup_prices + [100.0]), in_position=False)
    assert d.signal is Signal.HOLD


def test_long_only_no_short_on_spike(strategy, make_candles, warmup_prices):
    d = strategy.evaluate(make_candles(warmup_prices + [110.0]), in_position=False)
    assert d.signal is Signal.HOLD  # δεν σορτάρουμε


def test_exit_on_revert(strategy, make_candles, warmup_prices):
    d = strategy.evaluate(make_candles(warmup_prices + [110.0]), in_position=True)
    assert d.signal is Signal.SELL and d.z_score >= 0


def test_hold_position_below_mean(strategy, make_candles, warmup_prices):
    d = strategy.evaluate(make_candles(warmup_prices + [90.0]), in_position=True)
    assert d.signal is Signal.HOLD


def test_deterministic(strategy, make_candles, warmup_prices):
    c = make_candles(warmup_prices + [110.0])
    assert strategy.evaluate(c, in_position=True) == strategy.evaluate(c, in_position=True)
