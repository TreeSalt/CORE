from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr
from antigravity_harness.strategies.base import Strategy

# Hardcoded parameters removed. Now using params.


class V080VolatilityGuardTrend(Strategy):
    """
    Tier 2: Volatility Guard Trend
    Entry: Trend + Momentum AND Volatility within Safe Band
    Exit: Trend Reversal OR Stop
    """

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:

        # Trend
        df["sma"] = df["Close"].rolling(params.ma_length).mean()

        # Momentum (ROC or simple change)
        # using ma_fast as proxy for momentum lookback
        df["mom"] = df["Close"].pct_change(params.ma_fast)

        # Volatility (ATR %)
        # using rsi_length (14) as proxy for ATR period
        df["ATR"] = atr(df, params.rsi_length)
        df["atr_pct"] = df["ATR"] / df["Close"]

        # Conditions
        trend_up = df["Close"] > df["sma"]
        mom_up = df["mom"] > 0

        # Guard
        vol_safe = (df["atr_pct"] < params.vol_max_pct) & (df["atr_pct"] > params.vol_min_pct)

        # Signals
        df["entry_signal"] = (trend_up & mom_up & vol_safe).fillna(False).astype(bool)

        # Exit (Trend Reversal)
        reversal = df["Close"] < df["sma"]
        df["exit_signal"] = reversal.fillna(False).astype(bool)

        return df

    def generate_signal(self, row: pd.Series, params: StrategyParams) -> Dict[str, Any]:
        return {}
