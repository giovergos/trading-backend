"""Κύκλος ζωής του Ethereum client (web3.py async). Προαιρετικό."""
import logging

from web3 import AsyncHTTPProvider, AsyncWeb3

from app.config import get_settings

log = logging.getLogger(__name__)

_w3: AsyncWeb3 | None = None


def init_web3() -> AsyncWeb3 | None:
    global _w3
    url = get_settings().eth_rpc_url
    if not url:
        log.info("ETH_RPC_URL δεν έχει οριστεί — on-chain συλλογή απενεργοποιημένη.")
        _w3 = None
        return None
    _w3 = AsyncWeb3(AsyncHTTPProvider(url))
    return _w3


async def close_web3() -> None:
    global _w3
    _w3 = None


def get_web3() -> AsyncWeb3:
    if _w3 is None:
        raise RuntimeError("Ethereum client δεν είναι διαθέσιμος")
    return _w3


def is_enabled() -> bool:
    return _w3 is not None
