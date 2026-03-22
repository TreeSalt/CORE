from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from mantis_core.config import StrategyParams
from mantis_core.indicators import atr, sma
from mantis_core.strategies.base import Strategy


class V100ConsensualMomentum(Strategy):
    """
    Sovereign Tier Strategy: Consensual Momentum (v100).
    Only executes if technical momentum is confirmed by intellectual consensus.

    Logic:
    1. Technical: Close > SMA(ma_length)
    2. Intellectual: Consensus Signal > 0.3 AND Confidence > 0.7
    3. Inverse Guard: Exit if Consensus < 0 (Regime Flip)
    """

    name = "v100_consensual_momentum"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA"] = sma(out["Close"], int(params.ma_length))
        out["ATR"] = atr(out, 14)

        # 2. Consensus Extraction
        consensus = 0.0
        confidence = 0.0
        
        if intelligence:
            consensus = float(intelligence.get("consensus", 0.0))
            confidence = float(intelligence.get("confidence", 0.0))

        out["consensus_signal"] = consensus
        out["consensus_confidence"] = confidence

        # 3. Strategy Logic
        # Technical Trend
        trend_ok = out["Close"] > out["SMA"]

        # Intellectual Consensus
        # We require at least moderate bullish consensus and high confidence
        intel_ok = (out["consensus_signal"] > 0.3) & (out["consensus_confidence"] > 0.7)

        # Final Entry: Technical AND Intellectual
        out["entry_signal"] = (trend_ok & intel_ok).fillna(False).astype(bool)

        # 4. Exit Logic: Price cross SMA OR Consensus becomes bearish
        exit_condition = (out["Close"] < out["SMA"]) | (out["consensus_signal"] < 0)
        out["exit_signal"] = exit_condition.fillna(False).astype(bool)

        return out
