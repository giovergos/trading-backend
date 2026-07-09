"""Backtesting engine.

Τρέχει τον ΙΔΙΟ πυρήνα στρατηγικής (MeanReversionStrategy) πάνω σε ιστορικά
κεριά, προσομοιώνοντας long-only συναλλαγές. Σε κάθε βήμα καλεί
strategy.evaluate(candles[:i+1], in_position), δηλαδή την πανομοιότυπη λογική
που θα τρέξει και ο live executor — αυτό εγγυάται συνέπεια backtest ≡ live.

Σχεδιαστικές παραδοχές (για αποφυγή look-ahead bias):
  * Το σήμα στη μπάρα i υπολογίζεται από δεδομένα έως & με τη μπάρα i, αλλά
    η εκτέλεση γίνεται στο OPEN της επόμενης μπάρας (i+1). Δεν συναλλάσσεσαι
    στην τιμή που μόλις χρησιμοποίησες για την απόφαση.
  * Long-only, μία θέση τη φορά, all-in (όλο το διαθέσιμο κεφάλαιο).
  * Προαιρετική προμήθεια (fee_rate) σε είσοδο & έξοδο.
"""
import math
import statistics

from app.models.backtest import BacktestMetrics, BacktestReport, Trade
from app.models.market import Candle
from app.strategy.mean_reversion import MeanReversionStrategy, Signal

_UNIT_MINUTES = {"m": 1, "h": 60, "d": 1440, "w": 10080}


def periods_per_year(timeframe: str) -> float:
    tf = timeframe.strip().lower()
    num = int("".join(ch for ch in tf if ch.isdigit()) or 1)
    unit = "".join(ch for ch in tf if ch.isalpha()) or "h"
    minutes = num * _UNIT_MINUTES.get(unit, 60)
    return (365 * 24 * 60) / minutes


def max_drawdown_pct(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        if peak > 0:
            max_dd = max(max_dd, (peak - e) / peak)
    return max_dd * 100


def sharpe_ratio(equity: list[float], ppy: float) -> float:
    if len(equity) < 2:
        return 0.0
    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)) if equity[i - 1] > 0]
    if len(rets) < 2:
        return 0.0
    sd = statistics.pstdev(rets)
    if sd == 0:
        return 0.0
    return (statistics.fmean(rets) / sd) * math.sqrt(ppy)


class Backtester:
    def __init__(self, strategy: MeanReversionStrategy, initial_capital: float = 10_000.0,
                 fee_rate: float = 0.0):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate

    def run(self, candles: list[Candle]) -> BacktestReport:
        n = len(candles)
        cash = self.initial_capital
        units = 0.0
        entry_price = 0.0
        entry_time = None
        trades: list[Trade] = []
        equity_curve: list[float] = []

        for i in range(n):
            c = candles[i]
            equity_curve.append(cash + units * c.close)
            decision = self.strategy.evaluate(candles[: i + 1], in_position=units > 0)
            if i + 1 >= n:
                break  # δεν υπάρχει επόμενη μπάρα για εκτέλεση
            exec_price = candles[i + 1].open

            if decision.signal is Signal.BUY and units == 0:
                invest = cash * (1 - self.fee_rate)
                units = invest / exec_price
                entry_price = exec_price
                entry_time = candles[i + 1].timestamp
                cash = 0.0
            elif decision.signal is Signal.SELL and units > 0:
                proceeds = units * exec_price * (1 - self.fee_rate)
                cost = units * entry_price
                trades.append(Trade(
                    symbol=c.symbol, entry_time=entry_time, entry_price=entry_price,
                    exit_time=candles[i + 1].timestamp, exit_price=exec_price,
                    pnl=proceeds - cost,
                    return_pct=((proceeds - cost) / cost * 100) if cost else 0.0,
                ))
                cash = proceeds
                units = 0.0

        final_equity = equity_curve[-1] if equity_curve else self.initial_capital
        ppy = periods_per_year(candles[0].timeframe) if candles else 8760.0
        wins = sum(1 for t in trades if t.pnl > 0)

        metrics = BacktestMetrics(
            total_return_pct=(final_equity - self.initial_capital) / self.initial_capital * 100,
            max_drawdown_pct=max_drawdown_pct(equity_curve),
            sharpe_ratio=sharpe_ratio(equity_curve, ppy),
            win_rate=(wins / len(trades) * 100) if trades else 0.0,
            num_trades=len(trades),
        )
        return BacktestReport(
            symbol=candles[0].symbol if candles else "",
            timeframe=candles[0].timeframe if candles else "",
            initial_capital=self.initial_capital,
            final_equity=final_equity,
            start=candles[0].timestamp if candles else None,
            end=candles[-1].timestamp if candles else None,
            metrics=metrics,
            trades=trades,
        )
