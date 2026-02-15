from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr, rsi, sma
from antigravity_harness.strategies.base import Strategy


class V050TrendMomentum(Strategy):
    """v050_trend_momentum: Long Only Trend Following with RSI Momentum.

    Logic:
      Entry: Close > SlowMA AND Close > FastMA AND RSI > rsi_entry
      Exit:  Close < FastMA OR RSI < rsi_exit
      Stop:  Fixed ATR stop (engine managed)
    """

    name = "v050_trend_momentum"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA_SLOW"] = sma(out["Close"], int(params.ma_length))
        out["SMA_FAST"] = sma(out["Close"], int(params.ma_fast))
        out["RSI"] = rsi(out["Close"], int(params.rsi_length))
        out["ATR"] = atr(out, 14)

        # 2. Logic Conditionals

        # A. Trend Filter (Dual MA)
        if params.disable_sma:
            trend_ok = pd.Series(True, index=out.index)
        else:
            # Macro Trend + Momentum Trend
            trend_ok = (out["Close"] > out["SMA_SLOW"]) & (out["Close"] > out["SMA_FAST"])

        # B. Momentum Entry (Strength)
        entry_rsi_ok = pd.Series(True, index=out.index) if params.disable_rsi else out["RSI"] > float(params.rsi_entry)

        # Signal
        out["entry_signal"] = (trend_ok & entry_rsi_ok).fillna(False).astype(bool)

        # 3. Exit Logic (Trend Break or Momentum Loss)
        exit_trend = out["Close"] < out["SMA_FAST"]
        exit_rsi = out["RSI"] < float(params.rsi_exit)

        out["exit_signal"] = (exit_trend | exit_rsi).fillna(False).astype(bool)

        return out
