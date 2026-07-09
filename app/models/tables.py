"""ORM σχήμα βάσης (SQLAlchemy 2.0 declarative)."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CandleORM(Base):
    """OHLCV κεριά. Σύνθετο PK (symbol, timeframe, timestamp) -> idempotency."""

    __tablename__ = "candles"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


class StablecoinTransferORM(Base):
    """Μεγάλες μεταφορές stablecoins. PK (tx_hash, log_index) -> idempotency."""

    __tablename__ = "onchain_transfers"

    tx_hash: Mapped[str] = mapped_column(String(66), primary_key=True)
    log_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(8))
    from_address: Mapped[str] = mapped_column(String(42))
    to_address: Mapped[str] = mapped_column(String(42))
    amount: Mapped[float] = mapped_column(Float)
    block_number: Mapped[int] = mapped_column(BigInteger)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
