from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from mantis_core.config import StrategyParams
from mantis_core.indicators import atr, sma
from mantis_core.strategies.base import Strategy


class V090EssenceFollower(Strategy):
    """
    The First Intelligent Strategy: Essence Follower.
    Uses "Market Pulse" sentiment gurgled from the raw aether to filter trades.

    Logic:
    1. Standard SMA Trend: Close > SMA(ma_length)
    2. Essence Filter: Market Sentiment must be > threshold

    Proof of Concept for the Data Gurgling Phase.
    """

    name = "v090_essence_follower"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA"] = sma(out["Close"], int(params.ma_length))
        out["ATR"] = atr(out, 14)

        # 2. Essence Extraction
        # Default sentiment to 0 if no intelligence is provided
        sentiment = 0.0
        if intelligence and "sentiment" in intelligence:
            sentiment = float(intelligence["sentiment"])
            # In a real backtest, this sentiment would vary per-bar.
            # In our current "Gurgler", it's a single latest-value injection.
            # We broadcast it to all rows to simulate 'Global Context Awareness'.

        out["sentiment_signal"] = sentiment

        # 3. Strategy Logic
        # Trend: Price > SMA
        trend_ok = out["Close"] > out["SMA"]

        # Essence: Sentiment must be non-extreme fear (>-0.2)
        # Fear & Greed maps: 0 (Extreme Fear) -> 100 (Extreme Greed)
        # Normalized: -1.0 -> 1.0.
        # -0.2 corresponds to 40 on F&G index.
        essence_ok = out["sentiment_signal"] > -0.2

        # Final Entry: Trend AND Essence
        out["entry_signal"] = (trend_ok & essence_ok).fillna(False).astype(bool)

        # 4. Exit Logic
        out["exit_signal"] = (out["Close"] < out["SMA"]).fillna(False).astype(bool)

        return out
