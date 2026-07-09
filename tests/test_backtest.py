"""Tests μηχανής backtesting & μετρικών."""
from app.backtesting.engine import (
    Backtester, max_drawdown_pct, periods_per_year, sharpe_ratio,
)
from app.strategy.mean_reversion import MeanReversionStrategy


def test_max_drawdown():
    assert abs(max_drawdown_pct([100, 120, 90, 110]) - 25.0) < 1e-9


def test_sharpe_zero_variance():
    assert sharpe_ratio([100, 110, 121], ppy=1.0) == 0.0  # σταθερές αποδόσεις -> std 0


def test_sharpe_known_value():
    assert abs(sharpe_ratio([100, 110, 105], ppy=1.0) - 0.375) < 1e-3


def test_periods_per_year():
    assert periods_per_year("1h") == 8760
    assert periods_per_year("1d") == 365
    assert periods_per_year("15m") == 35040


def test_profitable_roundtrip(make_candles):
    warmup = [99.0 if i % 2 == 0 else 101.0 for i in range(20)]
    prices = warmup + [90.0, 92.0, 96.0, 101.0, 105.0, 108.0, 108.0, 108.0]
    bt = Backtester(MeanReversionStrategy(20, 2.0, 0.0), initial_capital=10_000.0, fee_rate=0.001)
    rep = bt.run(make_candles(prices))
    assert rep.metrics.num_trades == 1
    assert rep.metrics.total_return_pct > 0
    assert rep.metrics.win_rate == 100.0
    assert rep.trades[0].exit_price > rep.trades[0].entry_price


def test_empty_candles_no_crash(make_candles):
    bt = Backtester(MeanReversionStrategy(20, 2.0, 0.0))
    rep = bt.run([])
    assert rep.metrics.num_trades == 0
