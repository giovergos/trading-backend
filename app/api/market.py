"""Endpoints δεδομένων αγοράς."""
from fastapi import APIRouter, HTTPException, Query, Request

from app.config import get_settings
from app.models.market import Candle, Ticker

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/ohlcv", response_model=list[Candle])
async def get_ohlcv(
    request: Request,
    symbol: str = Query("BTC/USDT"),
    timeframe: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Candle]:
    """Ιστορικά OHLCV κεριά (REST) για ένα σύμβολο."""
    collector = request.app.state.collector
    tf = timeframe or get_settings().timeframe
    try:
        return await collector.fetch_ohlcv(symbol, tf, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Σφάλμα exchange: {exc}")


@router.get("/latest", response_model=list[Ticker])
async def get_latest(request: Request) -> list[Ticker]:
    """Τελευταίες live τιμές από τη WebSocket ροή (in-memory, Φάση 1)."""
    return request.app.state.collector.store.all()
