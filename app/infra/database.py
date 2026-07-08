"""Ασύγχρονη πρόσβαση σε PostgreSQL μέσω SQLAlchemy 2.0 + asyncpg.

Σχεδιαστική επιλογή: το engine αρχικοποιείται/καταστρέφεται ρητά στο lifespan
της εφαρμογής (όχι σε import time), ώστε οι συνδέσεις να ανοίγουν όταν είναι
έτοιμη η βάση και να κλείνουν καθαρά στο shutdown.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    settings = get_settings()
    _engine = create_async_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,   # αποφεύγει "stale" συνδέσεις
        future=True,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Factory για AsyncSession — θα το χρησιμοποιούν τα modules επόμενων φάσεων."""
    if _sessionmaker is None:
        raise RuntimeError("Database engine δεν έχει αρχικοποιηθεί")
    return _sessionmaker


async def ping() -> bool:
    """Έλεγχος συνδεσιμότητας για το /health (δεν πετάει exception)."""
    if _engine is None:
        return False
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
