"""ORM σχήμα βάσης (SQLAlchemy 2.0 declarative).

Ο πίνακας candles αντικατοπτρίζει ένα-προς-ένα το domain μοντέλο Candle.
Σύνθετο πρωτεύον κλειδί (symbol, timeframe, timestamp): ένα κερί ταυτοποιείται
μοναδικά από αυτά τα τρία, οπότε το ίδιο το κλειδί εγγυάται ότι δεν μπαίνουν
διπλότυπα — κρίσιμο για idempotent backfill.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CandleORM(Base):
    __tablename__ = "candles"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
