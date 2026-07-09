"""Domain μοντέλα backtesting: συναλλαγές, μετρικές, αναφορά."""
from datetime import datetime

from pydantic import BaseModel


class Trade(BaseModel):
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl: float
    return_pct: float


class BacktestMetrics(BaseModel):
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    num_trades: int


class BacktestReport(BaseModel):
    symbol: str
    timeframe: str
    initial_capital: float
    final_equity: float
    start: datetime | None
    end: datetime | None
    metrics: BacktestMetrics
    trades: list[Trade]
