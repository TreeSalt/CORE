"""Crypto exchange adapter — stub implementation for MANTIS data pipeline."""
import time
import random
import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

SUPPORTED_TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")
SUPPORTED_SYMBOLS = ("BTC_USDT", "ETH_USDT", "SOL_USDT", "AVAX_USDT", "LINK_USDT")


@dataclass
class AdapterConfig:
    max_requests_per_minute: int = 60
    max_retries: int = 3
    backoff_base: float = 1.0


class CryptoExchangeAdapter:
    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self._connected = False
        self._request_count = 0
        self._last_reset = time.time()

    def connect(self, config_dict: dict) -> None:
        self._connected = True
        log.info("Adapter connected (stub mode)")

    def disconnect(self) -> None:
        self._connected = False
        log.info("Adapter disconnected")

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list:
        if symbol not in SUPPORTED_SYMBOLS:
            raise ValueError(f"Unsupported symbol: {symbol}")
        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        self._enforce_rate_limit()
        return [self._generate_mock_candle(symbol, i) for i in range(limit)]

    def _enforce_rate_limit(self) -> None:
        now = time.time()
        if now - self._last_reset > 60:
            self._request_count = 0
            self._last_reset = now
        self._request_count += 1
        if self._request_count > self.config.max_requests_per_minute:
            sleep_time = 60 - (now - self._last_reset)
            if sleep_time > 0:
                log.warning(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            self._request_count = 0
            self._last_reset = time.time()

    @staticmethod
    def _generate_mock_candle(symbol: str, index: int) -> dict:
        base_price = {"BTC_USDT": 65000, "ETH_USDT": 3400, "SOL_USDT": 140,
                      "AVAX_USDT": 35, "LINK_USDT": 15}.get(symbol, 100)
        noise = random.uniform(-0.02, 0.02)
        o = base_price * (1 + noise)
        h = o * (1 + random.uniform(0, 0.01))
        l = o * (1 - random.uniform(0, 0.01))
        c = random.uniform(l, h)
        return {"timestamp": 1700000000 + index * 60, "open": round(o, 2),
                "high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
                "volume": round(random.uniform(100, 10000), 2)}
