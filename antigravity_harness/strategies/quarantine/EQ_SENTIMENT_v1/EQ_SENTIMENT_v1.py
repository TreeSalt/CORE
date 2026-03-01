"""
antigravity_harness/strategies/quarantine/EQ_SENTIMENT_v1/EQ_SENTIMENT_v1.py
MISSION v4.5.370: Proof Strategy — Equity Sentiment v1.
Reads orthogonal sentiment_score from intelligence dict, emits signals.
Quarantine-tier: NOT for production use.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from antigravity_harness.accelerators.vector_cache import VectorCache
from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr
from antigravity_harness.strategies.base import Strategy


class EQSentimentV1(Strategy):
    """Equity Sentiment v1 — Quarantine Proof Strategy.

    Reads `intelligence["sentiment"]` (pd.Series, -1.0 to 1.0).
    Long entry when sentiment > entry_threshold (default 0.5).
    Exit when sentiment < exit_threshold (default -0.2).
    ATR is computed for stop/sizing (required by Strategy contract).

    FAIL-SAFE: If intelligence is None or "sentiment" key is missing,
    all signals default to False (no trades).
    """

    name = "EQ_SENTIMENT_v1"

    ENTRY_THRESHOLD = 0.5
    EXIT_THRESHOLD = -0.2
    ATR_LENGTH = 14

    def prepare_data(
        self,
        df: pd.DataFrame,
        params: StrategyParams,
        intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[VectorCache] = None,
    ) -> pd.DataFrame:
        out = df.copy()

        # ATR is REQUIRED by the Strategy contract
        if vector_cache is not None:
            atr_s = vector_cache.get("ATR", self.ATR_LENGTH)
            if atr_s is None:
                atr_s = atr(out, self.ATR_LENGTH)
                vector_cache.put("ATR", self.ATR_LENGTH, atr_s)
            out["ATR"] = atr_s
        else:
            out["ATR"] = atr(out, self.ATR_LENGTH)

        # FAIL-SAFE: No intelligence → no signals
        if intelligence is None or "sentiment" not in intelligence:
            out["entry_signal"] = False
            out["exit_signal"] = False
            out["sentiment_score"] = np.nan
            return out

        # Extract sentiment (already lagged and aligned by SentimentFeed.as_dict)
        sentiment: pd.Series = intelligence["sentiment"]

        # Align sentiment to our bar index via forward-fill
        aligned = sentiment.reindex(out.index, method="ffill")
        out["sentiment_score"] = aligned

        # Signal Logic
        out["entry_signal"] = (aligned > self.ENTRY_THRESHOLD).fillna(False).astype(bool)
        out["exit_signal"] = (aligned < self.EXIT_THRESHOLD).fillna(False).astype(bool)

        return out

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tier": "quarantine",
            "entry_threshold": self.ENTRY_THRESHOLD,
            "exit_threshold": self.EXIT_THRESHOLD,
            "data_dependency": "orthogonal:sentiment_score",
            "provenance_required": True,
        }
