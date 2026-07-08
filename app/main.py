"""Σημείο εισόδου της εφαρμογής FastAPI."""
import logging

from fastapi import FastAPI

from app.api import health, market
from app.config import get_settings
from app.core.lifespan import lifespan

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(market.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"service": settings.app_name, "environment": settings.environment}
