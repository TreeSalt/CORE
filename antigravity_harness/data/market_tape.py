"""
antigravity_harness/data/market_tape.py
=======================================
Deterministic MarketTape logic for TRADER_OPS.

Provides the canonical container for bar data, ensuring that the 'data_hash' 
is computed consistently regardless of row ordering or metadata variations 
in the source CSV.

Schema:
    timestamp_utc: ISO8601 (UTC)
    open, high, low, close: float
    volume: float
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


class MarketTape:
    """Canonical container for deterministic market data."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with a DataFrame. 
        Expected columns: ['open', 'high', 'low', 'close', 'volume'].
        Index: DatetimeIndex (UTC).
        """
        self.df = df.sort_index()

    @classmethod
    def from_csv(cls, path: Path | str) -> MarketTape:
        """Load from CSV with strict schema enforcement."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"MarketTape source missing: {p}")

        df = pd.read_csv(p)
        
        # Normalize headers to lowercase
        df.columns = [c.lower() for c in df.columns]
        
        if "timestamp_utc" in df.columns:
            df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
            df.set_index("timestamp_utc", inplace=True)
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df.set_index("timestamp", inplace=True)
        else:
            # Try index 0 if it looks like a date
            df.index = pd.to_datetime(df.index, utc=True)

        # Enforce required columns
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"MarketTape missing required columns: {missing}")

        return cls(df[list(required)])

    @property
    def data_hash(self) -> str:
        """
        Compute deterministic SHA-256 of the data content.
        Rounds floats to 8 decimal places and converts to a stable JSON string.
        """
        if self.df.empty:
            return hashlib.sha256(b"{}").hexdigest()

        # Deterministic serialization:
        # 1. Round to 8 decimals to avoid floating point drift across hardware
        # 2. Convert to list of dicts
        # 3. Sort by timestamp (index)
        # 4. JSON dump with sort_keys=True
        data_to_hash = self.df.round(8).copy()
        data_to_hash["timestamp"] = data_to_hash.index.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create a stable list of records
        records = data_to_hash.to_dict("records")
        # Ensure timestamp is the first key in the string for human readability if needed
        # but sort_keys in json.dumps handles the actual determinism.
        
        content = json.dumps(records, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_csv(self, path: Path | str) -> None:
        """Save tape to CSV matching the canonical schema."""
        output = self.df.copy()
        output.index.name = "timestamp_utc"
        output.to_csv(path)
