from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr, rsi, sma
from antigravity_harness.strategies.base import Strategy


class V032Simple(Strategy):
    """Baseline: SMA trend filter + RSI oversold + ATR stop.

    Long:
      Close > SMA(ma_length) AND RSI(rsi_length) < rsi_entry
    Exit:
      Close < SMA(ma_length) OR RSI(rsi_length) > rsi_exit
    Stop:
      entry - stop_atr * ATR
    """

    name = "v032_simple"

    def prepare_data(
        self, df: pd.DataFrame, params: StrategyParams, intelligence: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators
        out["SMA"] = sma(out["Close"], int(params.ma_length))
        out["RSI"] = rsi(out["Close"], int(params.rsi_length))
        out["ATR"] = atr(out, 14)

        # 2. Logic Conditionals (Raw)

        # SMA Condition
        sma_cond = pd.Series(True, index=out.index) if params.disable_sma else out["Close"] > out["SMA"]

        # RSI Entry Condition
        if params.disable_rsi:
            rsi_entry_cond = pd.Series(True, index=out.index)
        else:
            rsi_entry_cond = out["RSI"] < float(params.rsi_entry)

        # Long Signal: ALL Valid
        long_signal = (sma_cond & rsi_entry_cond).fillna(False)
        out["entry_signal"] = long_signal.astype(bool)

        # 3. Exit Logic
        exit_sma = out["Close"] < out["SMA"]
        exit_rsi = out["RSI"] > float(params.rsi_exit)

        out["exit_signal"] = (exit_sma | exit_rsi).fillna(False).astype(bool)

        return out
