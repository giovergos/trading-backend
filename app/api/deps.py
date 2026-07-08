"""Κοινές εξαρτήσεις (dependencies) για τα endpoints."""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra import database


async def get_session() -> AsyncIterator[AsyncSession]:
    sessionmaker = database.get_sessionmaker()
    async with sessionmaker() as session:
        yield session
