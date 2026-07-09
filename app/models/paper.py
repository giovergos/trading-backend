"""Domain μοντέλα paper trading."""
from datetime import datetime

from pydantic import BaseModel


class PaperPosition(BaseModel):
    """Ανοιχτή (long) θέση paper trading."""

    symbol: str
    units: float
    entry_price: float
    entry_time: datetime


class OpenPositionView(BaseModel):
    """Ανοιχτή θέση με mark-to-market (για το API)."""

    symbol: str
    units: float
    entry_price: float
    entry_time: datetime
    current_price: float | None
    unrealized_pnl: float | None


class PaperTrade(BaseModel):
    """Ολοκληρωμένη (κλεισμένη) paper συναλλαγή."""

    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl: float
    return_pct: float
