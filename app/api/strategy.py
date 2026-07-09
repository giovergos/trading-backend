"""Endpoint στρατηγικής: τρέχον signal για ένα σύμβολο."""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.infra import candles as candles_repo
from app.models.strategy import SignalReport

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/signal", response_model=SignalReport)
async def get_signal(
    request: Request,
    symbol: str = Query("BTC/USDT"),
    timeframe: str | None = Query(None),
    in_position: bool = Query(False, description="Τρέχουσα θέση (για λογική εξόδου)"),
    session: AsyncSession = Depends(get_session),
) -> SignalReport:
    """Τρέχει τον πυρήνα της στρατηγικής πάνω στα πιο πρόσφατα αποθηκευμένα κεριά."""
    strategy = request.app.state.strategy
    tf = timeframe or get_settings().timeframe
    candles = await candles_repo.get_candles(session, symbol, tf, strategy.window)
    decision = strategy.evaluate(candles, in_position=in_position)
    return SignalReport(
        symbol=symbol, timeframe=tf,
        signal=decision.signal.value, price=decision.price,
        mean=decision.mean, upper=decision.upper, lower=decision.lower,
        z_score=decision.z_score, window=strategy.window, num_std=strategy.num_std,
        reason=decision.reason,
        as_of=candles[-1].timestamp if candles else None,
    )
