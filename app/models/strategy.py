"""Domain μοντέλο αποτελέσματος στρατηγικής (για το API)."""
from datetime import datetime

from pydantic import BaseModel


class SignalReport(BaseModel):
    symbol: str
    timeframe: str
    signal: str            # BUY / SELL / HOLD
    price: float
    mean: float | None
    upper: float | None
    lower: float | None
    z_score: float | None
    window: int
    num_std: float
    reason: str
    as_of: datetime | None  # timestamp του τελευταίου κεριού
