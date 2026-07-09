"""Domain μοντέλα on-chain δεδομένων (contextual signals)."""
from datetime import datetime

from pydantic import BaseModel


class GasSnapshot(BaseModel):
    block_number: int
    base_fee_gwei: float
    gas_price_gwei: float
    gas_used: int
    gas_limit: int
    timestamp: datetime


class StablecoinTransfer(BaseModel):
    tx_hash: str
    log_index: int
    token: str
    from_address: str
    to_address: str
    amount: float
    block_number: int
    timestamp: datetime
