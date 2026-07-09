"""Tests αποκωδικοποίησης on-chain Transfer events."""
from hexbytes import HexBytes

from app.collectors.onchain import MAINNET_STABLECOINS, TRANSFER_TOPIC, decode_transfer

USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"


def _topic_addr(addr):
    return HexBytes("0x" + "00" * 12 + addr[2:])


def _log(token, units, decimals, tx, idx, block):
    return {
        "address": token,
        "topics": [TRANSFER_TOPIC,
                   _topic_addr("0x1111111111111111111111111111111111111111"),
                   _topic_addr("0x2222222222222222222222222222222222222222")],
        "data": HexBytes((units * 10 ** decimals).to_bytes(32, "big")),
        "transactionHash": HexBytes(tx),
        "logIndex": idx,
        "blockNumber": block,
    }


def test_decode_usdt_transfer():
    d = decode_transfer(_log(USDT, 2_000_000, 6, "0x" + "ab" * 32, 0, 100), MAINNET_STABLECOINS)
    assert d["token"] == "USDT" and d["amount"] == 2_000_000.0
    assert d["block_number"] == 100 and d["log_index"] == 0
    assert d["from_address"].lower().endswith("1111")


def test_decode_unknown_token_returns_none():
    log = _log("0x0000000000000000000000000000000000000000", 1, 6, "0x" + "cd" * 32, 0, 1)
    assert decode_transfer(log, MAINNET_STABLECOINS) is None
