from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr, rsi, sma
from antigravity_harness.strategies.base import Strategy


class V040AlphaPrime(Strategy):
    """Connors RSI Pullback (Mean Reversion in Trend).

    Concept: Buying deep pullbacks (low RSI) only when in a dominant trend (above SMA).

    Long:
      Close > SMA(ma_length) AND RSI(rsi_length) < rsi_entry
    Exit:
      Close < SMA(ma_length) OR RSI(rsi_length) > rsi_exit
    Stop:
      Managed by engine via stop_float * ATR
    """

    name = "v040_alpha_prime"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA"] = sma(out["Close"], int(params.ma_length))
        # Connors often uses very short RSI (2, 3), handled via params.rsi_length
        out["RSI"] = rsi(out["Close"], int(params.rsi_length))
        out["ATR"] = atr(out, 14)

        # 2. Logic Conditionals

        # A. Trend Filter
        trend_ok = pd.Series(True, index=out.index) if params.disable_sma else out["Close"] > out["SMA"]

        # B. Pullback Entry
        entry_ok = pd.Series(True, index=out.index) if params.disable_rsi else out["RSI"] < float(params.rsi_entry)

        # Signal
        out["entry_signal"] = (trend_ok & entry_ok).fillna(False).astype(bool)

        # 3. Exit Logic (Snap back or Trend Fail)
        # Note: Connors sometimes exits on Close > High(5) etc, but we stick to RSI Exit spec.

        exit_trend = out["Close"] < out["SMA"]
        exit_rsi = out["RSI"] > float(params.rsi_exit)

        out["exit_signal"] = (exit_trend | exit_rsi).fillna(False).astype(bool)

        return out
