"""Crypto WebSocket feed — stub returning mock data for MANTIS pipeline."""
import time
import random
import logging
from typing import Callable, Optional

log = logging.getLogger(__name__)


class CryptoWebSocketFeed:
    def __init__(self):
        self._connected = False
        self._subscriptions = []
        self._callback = None
        self._max_reconnects = 3
        self._backoff_seconds = 1.0

    def connect(self, config: dict) -> None:
        self._connected = True
        log.info("WebSocket feed connected (stub mode)")

    def disconnect(self) -> None:
        self._connected = False
        self._subscriptions = []
        log.info("WebSocket feed disconnected")

    def subscribe(self, symbols: list) -> None:
        self._subscriptions = list(symbols)
        log.info(f"Subscribed to {len(symbols)} symbols")

    def on_message(self, callback: Callable) -> None:
        self._callback = callback

    def poll(self) -> Optional[dict]:
        if not self._connected or not self._subscriptions:
            return None
        symbol = random.choice(self._subscriptions)
        msg_type = random.choice(["trade", "orderbook"])
        if msg_type == "trade":
            return self._mock_trade(symbol)
        return self._mock_orderbook(symbol)

    @staticmethod
    def _mock_trade(symbol: str) -> dict:
        base_prices = {"BTC_USDT": 65000, "ETH_USDT": 3400, "SOL_USDT": 140}
        price = base_prices.get(symbol, 100) * (1 + random.uniform(-0.001, 0.001))
        return {"type": "trade", "timestamp": int(time.time()),
                "symbol": symbol, "price": round(price, 2),
                "qty": round(random.uniform(0.01, 10), 4),
                "side": random.choice(["buy", "sell"])}

    @staticmethod
    def _mock_orderbook(symbol: str) -> dict:
        base = {"BTC_USDT": 65000, "ETH_USDT": 3400, "SOL_USDT": 140}.get(symbol, 100)
        mid = base * (1 + random.uniform(-0.001, 0.001))
        bids = [[round(mid - i * 0.5, 2), round(random.uniform(0.1, 5), 3)] for i in range(5)]
        asks = [[round(mid + i * 0.5, 2), round(random.uniform(0.1, 5), 3)] for i in range(5)]
        return {"type": "orderbook", "timestamp": int(time.time()),
                "symbol": symbol, "bids": bids, "asks": asks}
