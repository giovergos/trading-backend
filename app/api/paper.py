"""Endpoints paper trading: ανοιχτές θέσεις, ιστορικό συναλλαγών, σύνοψη PnL."""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.infra import paper_trades as trades_repo
from app.models.paper import OpenPositionView, PaperTrade

router = APIRouter(prefix="/paper", tags=["paper"])


@router.get("/positions", response_model=list[OpenPositionView])
async def get_positions(request: Request) -> list[OpenPositionView]:
    """Ανοιχτές θέσεις με mark-to-market (τρέχουσα τιμή από Redis)."""
    store = request.app.state.position_store
    ticker_cache = request.app.state.ticker_cache
    views: list[OpenPositionView] = []
    for pos in await store.get_all():
        ticker = await ticker_cache.get(pos.symbol)
        price = ticker.price if ticker else None
        unrealized = (price - pos.entry_price) * pos.units if price is not None else None
        views.append(OpenPositionView(
            symbol=pos.symbol, units=pos.units, entry_price=pos.entry_price,
            entry_time=pos.entry_time, current_price=price, unrealized_pnl=unrealized,
        ))
    return views


@router.get("/trades", response_model=list[PaperTrade])
async def get_trades(limit: int = Query(50, ge=1, le=500),
                     session: AsyncSession = Depends(get_session)) -> list[PaperTrade]:
    return await trades_repo.get_trades(session, limit)


@router.get("/summary")
async def get_summary(session: AsyncSession = Depends(get_session)) -> dict:
    """Σύνοψη realized PnL, πλήθος συναλλαγών, win rate."""
    return await trades_repo.pnl_summary(session)
