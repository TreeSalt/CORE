from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr
from antigravity_harness.strategies.base import Strategy

# Hardcoded parameters for v3.4 compliance (No new params allowed in StrategyParams)
DONCHIAN_PERIOD = 20
SMA_FILTER_PERIOD = 200
ATR_PERIOD = 14
STOP_ATR_MULT = 2.0


class V070DonchianBreakout(Strategy):
    """
    Tier 1: Donchian Breakout
    Entry: Close > Rolling High(N) AND Close > SMA(M)
    Exit: Close < Rolling Low(N) OR ATR Stop
    """

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        # Specific strategy constants override generic params.

        # Indicators
        df["high_rolling"] = df["High"].rolling(DONCHIAN_PERIOD).max().shift(1)
        df["low_rolling"] = df["Low"].rolling(DONCHIAN_PERIOD).min().shift(1)
        df["sma_filter"] = df["Close"].rolling(SMA_FILTER_PERIOD).mean()

        # ATR for stop loss (if dynamic)
        df["ATR"] = atr(df, ATR_PERIOD)

        # Signals
        # Long Entry
        # Note: shift(1) for donchian usually implies "breakout of previous N bars".
        # Current bar close > previous N bars high.

        breakout_up = df["Close"] > df["high_rolling"]
        trend_ok = df["Close"] > df["sma_filter"]

        df["entry_signal"] = (breakout_up & trend_ok).fillna(False).astype(bool)

        # Exit Signal (Breakout Down)
        breakout_down = df["Close"] < df["low_rolling"]
        df["exit_signal"] = breakout_down.fillna(False).astype(bool)

        return df

    def generate_signal(self, row: pd.Series, params: StrategyParams) -> Dict[str, Any]:
        # Not used in vector engine usually, but good for completeness
        return {}
