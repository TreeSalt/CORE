"""
antigravity_harness/data/sentiment_feed.py
MISSION v4.5.370: Orthogonal Sentiment Data Feed.
Provides a fail-closed interface for loading and injecting sentiment data.
"""
import hashlib
from pathlib import Path

import pandas as pd

from antigravity_harness.data_loader import ZeroCopyLoader


class SentimentFeed:
    """
    Feeds auxiliary sentiment data into the TRADER_OPS physics engine context.
    Expects a pandas Series aligned to the main price asset index,
    with scores from -1.0 to 1.0.

    MISSION v4.5.370: Enforces anti-lookahead lag rule and real data provenance.
    NEVER generates synthetic sentiment data.
    """

    def __init__(self, data: pd.Series, provenance_hash: str = "UNKNOWN"):
        if not isinstance(data, pd.Series):
            raise ValueError("SentimentFeed requires a pandas Series")
        self.data = data
        self.provenance_hash = provenance_hash

    @classmethod
    def from_csv(
        cls,
        path: Path,
        lag_seconds: int = 300,
        timestamp_col: str = "timestamp",
        value_col: str = "sentiment_score",
    ) -> "SentimentFeed":
        """
        Load sentiment data from a local CSV with provenance verification.
        Raises FileNotFoundError if the file is missing → BLOCKED_NO_ALT_DATA.
        """
        series = ZeroCopyLoader.load_orthogonal_csv(
            path=path,
            timestamp_col=timestamp_col,
            value_col=value_col,
            lag_seconds=lag_seconds,
        )
        # Compute provenance hash
        _raw_json = series.to_json(None, orient="values")  # type: ignore[call-overload]
        # MISSION v4.5.380: Definitive type narrowing for Mypy
        data_str: str = _raw_json if _raw_json is not None else "[]"
        provenance = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        return cls(data=series, provenance_hash=provenance)

    def inject_to_context(self, context) -> None:
        """Injects this feed into a generic context.intelligence dictionary."""
        if not hasattr(context, "intelligence") or context.intelligence is None:
            context.intelligence = {}
        context.intelligence["sentiment"] = self.data

    def as_dict(self, bar_index: pd.DatetimeIndex) -> dict:
        """
        Return a dictionary suitable for the `intelligence` kwarg of Strategy.prepare_data.
        Performs as-of merge: for each bar timestamp, finds the most recent
        sentiment observation that is <= bar_ts (after lag).
        """
        aligned = self.data.reindex(bar_index, method="ffill")
        return {"sentiment": aligned, "sentiment_provenance": self.provenance_hash}

    @staticmethod
    def blocked_status() -> str:
        """Returns the canonical status when no real alt-data is available."""
        return "BLOCKED_NO_ALT_DATA"
