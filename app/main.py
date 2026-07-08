"""Σημείο εισόδου της εφαρμογής FastAPI."""
from fastapi import FastAPI

from app.api import health
from app.config import get_settings
from app.core.lifespan import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"service": settings.app_name, "environment": settings.environment}
