"""Σημείο εισόδου της εφαρμογής FastAPI."""
import logging

from fastapi import FastAPI

from app.api import backtest, health, market, onchain, strategy
from app.config import get_settings
from app.core.lifespan import lifespan

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.5.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(onchain.router)
app.include_router(strategy.router)
app.include_router(backtest.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"service": settings.app_name, "environment": settings.environment}
