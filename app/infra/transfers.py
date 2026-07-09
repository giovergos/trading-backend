"""Repository για μεγάλες μεταφορές stablecoins (idempotent)."""
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onchain import StablecoinTransfer
from app.models.tables import StablecoinTransferORM


async def save_transfers(session: AsyncSession, transfers: list[StablecoinTransfer]) -> int:
    if not transfers:
        return 0
    rows = [t.model_dump() for t in transfers]
    stmt = insert(StablecoinTransferORM).values(rows).on_conflict_do_nothing(
        index_elements=["tx_hash", "log_index"]
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount if result.rowcount is not None else 0


async def get_recent_transfers(session: AsyncSession, limit: int) -> list[StablecoinTransfer]:
    stmt = (
        select(StablecoinTransferORM)
        .order_by(StablecoinTransferORM.block_number.desc(),
                  StablecoinTransferORM.log_index.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        StablecoinTransfer(
            tx_hash=r.tx_hash, log_index=r.log_index, token=r.token,
            from_address=r.from_address, to_address=r.to_address, amount=r.amount,
            block_number=r.block_number, timestamp=r.timestamp,
        )
        for r in result.scalars().all()
    ]
