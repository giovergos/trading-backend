"""Repository για τον πίνακα candles: αποθήκευση & ανάκτηση.

Το save_candles χρησιμοποιεί INSERT ... ON CONFLICT DO NOTHING (PostgreSQL):
αν ένα κερί υπάρχει ήδη (ίδιο symbol/timeframe/timestamp), αγνοείται αντί να
πετάξει σφάλμα. Έτσι μπορούμε να ξανατρέχουμε backfill χωρίς διπλότυπα.
"""
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Candle
from app.models.tables import CandleORM


async def save_candles(session: AsyncSession, candles: list[Candle]) -> int:
    if not candles:
        return 0
    rows = [c.model_dump() for c in candles]
    stmt = insert(CandleORM).values(rows).on_conflict_do_nothing(
        index_elements=["symbol", "timeframe", "timestamp"]
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount if result.rowcount is not None else 0


async def get_candles(
    session: AsyncSession, symbol: str, timeframe: str, limit: int
) -> list[Candle]:
    """Επιστρέφει τα πιο πρόσφατα κεριά, σε αύξουσα χρονική σειρά."""
    stmt = (
        select(CandleORM)
        .where(CandleORM.symbol == symbol, CandleORM.timeframe == timeframe)
        .order_by(CandleORM.timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()  # παλαιότερο -> νεότερο
    return [
        Candle(
            symbol=r.symbol, timeframe=r.timeframe, timestamp=r.timestamp,
            open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume,
        )
        for r in rows
    ]
