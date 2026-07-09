"""Repository για κλεισμένες paper συναλλαγές."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import PaperTrade
from app.models.tables import PaperTradeORM


async def save_trade(session: AsyncSession, trade: PaperTrade) -> None:
    session.add(PaperTradeORM(**trade.model_dump()))
    await session.commit()


async def get_trades(session: AsyncSession, limit: int) -> list[PaperTrade]:
    stmt = select(PaperTradeORM).order_by(PaperTradeORM.id.desc()).limit(limit)
    result = await session.execute(stmt)
    return [
        PaperTrade(
            symbol=r.symbol, entry_time=r.entry_time, entry_price=r.entry_price,
            exit_time=r.exit_time, exit_price=r.exit_price, pnl=r.pnl, return_pct=r.return_pct,
        )
        for r in result.scalars().all()
    ]


async def pnl_summary(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.coalesce(func.sum(PaperTradeORM.pnl), 0.0)))
    count = await session.scalar(select(func.count(PaperTradeORM.id)))
    wins = await session.scalar(select(func.count()).where(PaperTradeORM.pnl > 0))
    return {
        "realized_pnl": float(total or 0.0),
        "num_trades": int(count or 0),
        "win_rate": (float(wins or 0) / count * 100) if count else 0.0,
    }
