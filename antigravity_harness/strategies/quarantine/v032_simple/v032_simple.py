from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.indicators import atr, rsi, sma
from antigravity_harness.strategies.base import Strategy
from antigravity_harness.accelerators.vector_cache import VectorCache


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
        self, 
        df: pd.DataFrame, 
        params: StrategyParams, 
        intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[VectorCache] = None
    ) -> pd.DataFrame:
        out = df.copy()

        # 1. Indicators (O(1) VectorCache Path)
        ma_len = int(params.ma_length)
        rsi_len = int(params.rsi_length)
        atr_len = 14
        
        if vector_cache is not None:
            # SMA
            sma_s = vector_cache.get("SMA", ma_len)
            if sma_s is None:
                sma_s = sma(out["Close"], ma_len)
                vector_cache.put("SMA", ma_len, sma_s)
            out["SMA"] = sma_s
            
            # RSI
            rsi_s = vector_cache.get("RSI", rsi_len)
            if rsi_s is None:
                rsi_s = rsi(out["Close"], rsi_len)
                vector_cache.put("RSI", rsi_len, rsi_s)
            out["RSI"] = rsi_s
            
            # ATR
            atr_s = vector_cache.get("ATR", atr_len)
            if atr_s is None:
                atr_s = atr(out, atr_len)
                vector_cache.put("ATR", atr_len, atr_s)
            out["ATR"] = atr_s
            
        else:
            out["SMA"] = sma(out["Close"], ma_len)
            out["RSI"] = rsi(out["Close"], rsi_len)
            out["ATR"] = atr(out, atr_len)


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
