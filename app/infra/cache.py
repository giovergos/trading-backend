"""Ασύγχρονη πρόσβαση σε Redis."""
import redis.asyncio as aioredis

from app.config import get_settings

_redis: aioredis.Redis | None = None


def init_redis() -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
    _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis client δεν έχει αρχικοποιηθεί")
    return _redis


async def ping() -> bool:
    if _redis is None:
        return False
    try:
        return bool(await _redis.ping())
    except Exception:
        return False
