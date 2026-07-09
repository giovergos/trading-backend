"""Συλλέκτης on-chain (Ethereum): gas snapshot -> Redis, μεγάλες μεταφορές -> Postgres."""
import asyncio
import logging
from datetime import datetime, timezone

from web3 import AsyncWeb3

from app.collectors.web3_client import get_web3
from app.infra.onchain_cache import GasCache
from app.infra.transfers import save_transfers
from app.models.onchain import GasSnapshot, StablecoinTransfer

log = logging.getLogger(__name__)

MAINNET_STABLECOINS: dict[str, tuple[str, int]] = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6),
}

TRANSFER_TOPIC = AsyncWeb3.keccak(text="Transfer(address,address,uint256)")


def decode_transfer(log: dict, token_map: dict[str, tuple[str, int]]) -> dict | None:
    meta = token_map.get(log["address"].lower())
    if meta is None:
        return None
    symbol, decimals = meta
    topics = log["topics"]
    if len(topics) < 3:
        return None
    from_addr = AsyncWeb3.to_checksum_address("0x" + bytes(topics[1])[-20:].hex())
    to_addr = AsyncWeb3.to_checksum_address("0x" + bytes(topics[2])[-20:].hex())
    amount = int.from_bytes(bytes(log["data"]), "big") / (10 ** decimals)
    return {
        "tx_hash": "0x" + bytes(log["transactionHash"]).hex(),
        "log_index": int(log["logIndex"]),
        "token": symbol,
        "from_address": from_addr,
        "to_address": to_addr,
        "amount": amount,
        "block_number": int(log["blockNumber"]),
    }


class OnChainCollector:
    def __init__(self, gas_cache: GasCache, sessionmaker, token_map, threshold, poll_interval, max_block_span):
        self.gas_cache = gas_cache
        self.sessionmaker = sessionmaker
        self.token_map = token_map
        self.token_addresses = [AsyncWeb3.to_checksum_address(a) for a in token_map]
        self.threshold = threshold
        self.poll_interval = poll_interval
        self.max_block_span = max_block_span
        self._last_block: int | None = None

    async def poll_once(self) -> tuple[GasSnapshot, list[StablecoinTransfer]]:
        w3 = get_web3()
        block = await w3.eth.get_block("latest")
        latest = block["number"]
        gas_price = await w3.eth.gas_price

        snapshot = GasSnapshot(
            block_number=latest,
            base_fee_gwei=(block.get("baseFeePerGas") or 0) / 1e9,
            gas_price_gwei=gas_price / 1e9,
            gas_used=block["gasUsed"],
            gas_limit=block["gasLimit"],
            timestamp=datetime.fromtimestamp(block["timestamp"], tz=timezone.utc),
        )
        await self.gas_cache.set(snapshot)

        from_block = latest if self._last_block is None else self._last_block + 1
        from_block = max(from_block, latest - self.max_block_span + 1)
        transfers: list[StablecoinTransfer] = []
        if from_block <= latest:
            logs = await w3.eth.get_logs({
                "fromBlock": from_block, "toBlock": latest,
                "address": self.token_addresses, "topics": [TRANSFER_TOPIC],
            })
            ts_cache: dict[int, datetime] = {latest: snapshot.timestamp}
            for lg in logs:
                d = decode_transfer(lg, self.token_map)
                if d is None or d["amount"] < self.threshold:
                    continue
                bn = d["block_number"]
                if bn not in ts_cache:
                    b = await w3.eth.get_block(bn)
                    ts_cache[bn] = datetime.fromtimestamp(b["timestamp"], tz=timezone.utc)
                transfers.append(StablecoinTransfer(**d, timestamp=ts_cache[bn]))
            if transfers:
                async with self.sessionmaker() as session:
                    await save_transfers(session, transfers)
                log.info("On-chain: %d μεγάλες μεταφορές", len(transfers))
        self._last_block = latest
        return snapshot, transfers

    async def run(self) -> None:
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("On-chain poll σφάλμα: %s", exc)
            await asyncio.sleep(self.poll_interval)
