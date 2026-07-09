"""Endpoints on-chain δεδομένων."""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.infra import transfers as transfers_repo
from app.models.onchain import GasSnapshot, StablecoinTransfer

router = APIRouter(prefix="/onchain", tags=["onchain"])


@router.get("/gas", response_model=GasSnapshot | None)
async def get_gas(request: Request) -> GasSnapshot | None:
    return await request.app.state.gas_cache.get()


@router.get("/transfers", response_model=list[StablecoinTransfer])
async def get_transfers(
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[StablecoinTransfer]:
    return await transfers_repo.get_recent_transfers(session, limit)
