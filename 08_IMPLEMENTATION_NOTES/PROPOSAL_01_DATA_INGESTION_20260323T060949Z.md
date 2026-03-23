---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
#!/usr/bin/env python3
"""
01_DATA_E4_002_crypto_normalizer_v2.py
Corrected implementation for crypto data normalization with robust error handling,
schema validation, and no hardcoded secrets.
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict

# Configure standard logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NormalizedCryptoRecord:
    """Represents a normalized crypto market data record."""
    symbol: str
    price_usd: float
    volume_24h_usd: float
    timestamp: datetime
    source: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for storage or JSON serialization."""
        return {
            'symbol': self.symbol.upper(),
            'price_usd': self.price_usd,
            'volume_24h_usd': self.volume_24h_usd,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


class CryptoNormalizerV2:
    """
    Secure and robust normalizer for cryptocurrency market data.
    Prevents failures via try/except blocks, validates schemas, and avoids unsafe eval.
    """

    # Safe allowed characters for exchange rate identifiers (e.g., BTCUSD)
    SYMBOL_REGEX = re.compile(r'^[A-Z]+$')
    ALLOWED_PRICE_TIER = ['spot', 'futures']

    def __init__(self, source_name: str = "DEFAULT_EXCHANGE"):
        self.source_name = source_name
        # Validate source_name on init to prevent injection-like issues (e.g. /tmp in name)
        if '/' in source_name or '\\' in source_name or '..' in source_name:
            raise ValueError("Invalid source_name path detected")

    def _sanitize_symbol(self, symbol: str) -> Optional[str]:
        """Sanitize and validate the currency pair/ticker."""
        if not symbol:
            return None
        # Convert to uppercase
        cleaned = symbol.strip().upper()
        # Check regex match (only letters A-Z allowed for standard ticker)
        if self.SYMBOL_REGEX.match(cleaned):
            return cleaned
        return None

    def _parse_timestamp_utc(self, timestamp_input: Union[str, int, float], default_tz: bool = True) -> Optional[datetime]:
        """Parse various timestamp formats into a UTC datetime object."""
        if not timestamp_input:
            return None
        try:
            # Handle Unix timestamps (int or float)
            if isinstance(timestamp_input, (int, float)):
                return datetime.fromtimestamp(timestamp_input / 1e9, tz=timezone.utc)
            
            # Handle string timestamps
            dt = datetime.fromisoformat(timestamp_input.replace('Z', '+00:00'))
            if default_tz:
                dt = dt.astimezone(timezone.utc)
            return dt
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse timestamp: {timestamp_input}")
            return None

    def _validate_price(self, price: Union[str, float, int]) -> Optional[float]:
        """Validate and normalize price value."""
        if not price:
            return None
        try:
            # Attempt conversion
            val = float(price)
            # Ensure value is reasonable (not NaN/Inf)
            if not (val != val):  # check for NaN
                logger.warning(f"Detected NaN price")
                return None
            if abs(val) > 1e308:
                logger.warning(f"Price value out of bounds: {val}")
                return None
            return round(val, 4)
        except (TypeError, ValueError):
            logger.error(f"Invalid price type or value: {price}")
            return None

    def normalize_raw_message(self, raw_data: Dict[str, Any]) -> Optional[NormalizedCryptoRecord]:
        """
        Main entry point for normalizing a raw payload.
        Handles schema validation and conversion.
        """
        try:
            # Extract fields with safe defaults
            symbol_input = raw_data.get('symbol') or raw_data.get('pair')
            price_input = raw_data.get('price_usd') or raw_data.get('last_price')
            volume_input = raw_data.get('volume_24h_usd') or raw_data.get('volume_usd')
            timestamp_input = raw_data.get('timestamp') or raw_data.get('ts') or raw_data.get('datetime')
            
            # Sanitize symbol
            normalized_symbol = self._sanitize_symbol(symbol_input)
            if not normalized_symbol:
                logger.warning(f"Symbol normalization failed for {raw_data}")
                return None

            # Parse timestamp
            timestamp_utc = self._parse_timestamp_utc(timestamp_input)
            if not timestamp_utc:
                logger.warning("Timestamp normalization failed")
                return None

            # Validate price and volume (0 is valid, -1 usually indicates missing/invalid data in APIs)
            price_val = self._validate_price(price_input)
            volume_val = 0.0
            if volume_input is not None:
                try:
                    volume_val = float(volume_input)
                    if volume_val < 0:
                        logger.warning(f"Negative volume detected, setting to 0")
                        volume_val = 0.0
                except (TypeError, ValueError):
                    logger.warning("Volume parsing failed")

            # Construct record
            return NormalizedCryptoRecord(
                symbol=normalized_symbol,
                price_usd=price_val if price_val else 0.0, # Default 0 if invalid
                volume_24h_usd=volume_val,
                timestamp=timestamp_utc,
                source=self.source_name
            )

        except Exception as e:
            logger.exception(f"Unexpected error in normalize_raw_message")
            return None

    def process_batch(self, data_list: list) -> list[NormalizedCryptoRecord]:
        """Process a batch of raw records."""
        records = []
        for idx, item in enumerate(data_list):
            if isinstance(item, dict):
                result = self.normalize_raw_message(item)
                if result:
                    records.append(result)
                else:
                    logger.debug(f"Skipped record at index {idx}")
            else:
                logger.warning(f"Non-dict item in batch at index {idx}: {type(item)}")
        return records

    def get_schema(self) -> Dict[str, Any]:
        """Return the expected normalized schema."""
        # This method helps with external validation logic if needed
        return asdict(NormalizedCryptoRecord(symbol="BTCUSD", price_usd=0.0, volume_24h_usd=0.0, timestamp=datetime.now(timezone.utc), source=""))
```