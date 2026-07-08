"""Κύκλος ζωής του ccxt client.

Χρησιμοποιούμε την ccxt.pro έκδοση: το ίδιο instance εξυπηρετεί REST
(fetch_ohlcv για ιστορικά) και WebSocket (watch_* για live ροή). Το instance
αρχικοποιείται στο lifespan και κλείνει καθαρά στο shutdown — αλλιώς μένουν
ανοιχτά sockets.
"""
import ccxt.pro as ccxtpro

from app.config import get_settings

_exchange: ccxtpro.Exchange | None = None


def init_exchange() -> ccxtpro.Exchange:
    global _exchange
    settings = get_settings()
    exchange_cls = getattr(ccxtpro, settings.exchange_id)
    _exchange = exchange_cls({"enableRateLimit": True})
    return _exchange


async def close_exchange() -> None:
    global _exchange
    if _exchange is not None:
        await _exchange.close()
    _exchange = None


def get_exchange() -> ccxtpro.Exchange:
    if _exchange is None:
        raise RuntimeError("Exchange client δεν έχει αρχικοποιηθεί")
    return _exchange
