from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr, rsi, sma
from antigravity_harness.strategies.base import Strategy


class V060BitUniCore(Strategy):
    """v060_bit_uni_core: Specialized Crypto Trend-Following (Titan Logic).

    Bridge the Gap:
    Optimized for high-drift assets (BTC/ETH) to increase frequency while maintaining alpha.

    Logic:
      Entry:
        1. Macro Trend: Close > SMA(200)
        2. Micro Trend: Close > SMA(50)
        3. Momentum: RSI(14) > rsi_entry (Aggressive)
      Exit:
        1. Close < SMA(50) OR RSI < rsi_exit
      Stop:
        ATR-based (Engine managed)
    """

    name = "v060_bit_uni_core"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA_SLOW"] = sma(out["Close"], int(params.ma_length))
        out["SMA_FAST"] = sma(out["Close"], int(params.ma_fast))
        out["RSI"] = rsi(out["Close"], int(params.rsi_length))
        out["ATR"] = atr(out, 14)

        # 2. Logic Conditionals

        # Macro + Micro Trend
        if params.disable_sma:
            trend_ok = pd.Series(True, index=out.index)
        else:
            # Flexible trend filters based on params
            trend_ok = (out["Close"] > out["SMA_SLOW"]) & (out["Close"] > out["SMA_FAST"])

        # Momentum Entry
        entry_rsi_ok = pd.Series(True, index=out.index) if params.disable_rsi else out["RSI"] > float(params.rsi_entry)

        # Signal
        out["entry_signal"] = (trend_ok & entry_rsi_ok).fillna(False).astype(bool)

        # 3. Exit Logic
        # Exit if micro trend breaks or momentum collapses
        exit_trend = out["Close"] < out["SMA_FAST"]
        exit_rsi = out["RSI"] < float(params.rsi_exit)

        out["exit_signal"] = (exit_trend | exit_rsi).fillna(False).astype(bool)

        return out
