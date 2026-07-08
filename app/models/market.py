"""Domain μοντέλα αγοράς.

Σχεδιαστική απόφαση: αντί να διακινούμε ωμές λίστες της ccxt
([timestamp, open, high, low, close, volume]), τις μετατρέπουμε αμέσως σε
typed αντικείμενα με validation. Έτσι τα υπόλοιπα modules (strategy,
backtesting) εξαρτώνται από σταθερό contract, όχι από τη μορφή της ccxt·
και τα πεδία του Candle ορίζουν ουσιαστικά το σχήμα της βάσης (Φάση 2).
"""
from datetime import datetime, timezone

from pydantic import BaseModel


class Candle(BaseModel):
    """Ένα OHLCV κερί για συγκεκριμένο σύμβολο & timeframe."""

    symbol: str
    timeframe: str
    timestamp: datetime  # ώρα ανοίγματος του κεριού (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_ccxt(cls, symbol: str, timeframe: str, row: list) -> "Candle":
        ts, o, h, l, c, v = row
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
            open=o, high=h, low=l, close=c, volume=v,
        )


class Ticker(BaseModel):
    """Στιγμιαία τιμή (last price) από live WebSocket ροή."""

    symbol: str
    price: float
    timestamp: datetime

    @classmethod
    def from_ccxt(cls, symbol: str, ticker: dict) -> "Ticker":
        ts = ticker.get("timestamp") or 0
        return cls(
            symbol=symbol,
            price=ticker["last"],
            timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
        )
