"""Endpoints δεδομένων αγοράς."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.infra import candles as candles_repo
from app.models.market import Candle, Ticker

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/ohlcv", response_model=list[Candle])
async def get_ohlcv(
    symbol: str = Query("BTC/USDT"),
    timeframe: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> list[Candle]:
    tf = timeframe or get_settings().timeframe
    return await candles_repo.get_candles(session, symbol, tf, limit)


@router.post("/backfill")
async def backfill(
    request: Request,
    symbol: str = Query("BTC/USDT"),
    timeframe: str | None = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tf = timeframe or get_settings().timeframe
    try:
        fetched = await request.app.state.collector.fetch_ohlcv(symbol, tf, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Σφάλμα exchange: {exc}")
    stored = await candles_repo.save_candles(session, fetched)
    return {"symbol": symbol, "timeframe": tf, "fetched": len(fetched), "stored": stored}


@router.get("/latest", response_model=list[Ticker])
async def get_latest(request: Request) -> list[Ticker]:
    return await request.app.state.ticker_cache.get_all()
