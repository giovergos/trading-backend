"""Domain μοντέλα αγοράς (Pydantic)."""
from datetime import datetime, timezone

from pydantic import BaseModel


class Candle(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_ccxt(cls, symbol: str, timeframe: str, row: list) -> "Candle":
        ts, o, h, l, c, v = row
        return cls(
            symbol=symbol, timeframe=timeframe,
            timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
            open=o, high=h, low=l, close=c, volume=v,
        )


class Ticker(BaseModel):
    symbol: str
    price: float
    timestamp: datetime

    @classmethod
    def from_ccxt(cls, symbol: str, ticker: dict) -> "Ticker":
        ts = ticker.get("timestamp") or 0
        return cls(
            symbol=symbol, price=ticker["last"],
            timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
        )
