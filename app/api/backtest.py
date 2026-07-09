"""Endpoint backtesting: τρέχει τη στρατηγική σε ιστορικά κεριά."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.backtesting.engine import Backtester
from app.config import get_settings
from app.infra import candles as candles_repo
from app.models.backtest import BacktestReport

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=None)
async def run_backtest(
    request: Request,
    symbol: str = Query("BTC/USDT"),
    timeframe: str | None = Query(None),
    limit: int = Query(500, ge=20, le=1000),
    fmt: str = Query("json", pattern="^(json|csv)$", alias="format"),
    session: AsyncSession = Depends(get_session),
):
    """Τρέχει το backtest πάνω στα αποθηκευμένα κεριά. format=json|csv."""
    settings = get_settings()
    tf = timeframe or settings.timeframe
    candles = await candles_repo.get_candles(session, symbol, tf, limit)
    if len(candles) < settings.strategy_window:
        raise HTTPException(
            status_code=422,
            detail=f"Ανεπαρκή κεριά ({len(candles)}) < window ({settings.strategy_window}). Κάνε backfill πρώτα.",
        )

    backtester = Backtester(
        strategy=request.app.state.strategy,
        initial_capital=settings.backtest_initial_capital,
        fee_rate=settings.backtest_fee_rate,
    )
    report: BacktestReport = backtester.run(candles)

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["entry_time", "entry_price", "exit_time", "exit_price", "pnl", "return_pct"])
        for t in report.trades:
            writer.writerow([t.entry_time.isoformat(), t.entry_price,
                             t.exit_time.isoformat(), t.exit_price, t.pnl, t.return_pct])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")

    return report
