"""
antigravity_harness/strategies/legacy/v050_trend_momentum.py
============================================================
LEGACY STRATEGY — Preserved for reference. DO NOT use for new development.

Status: DEPRECATED (v4.5.29)
Reason: Uses older StrategyBase contract instead of v050 IntentStrategy.
Migration: Rewrite using IntentStrategy from v050_base_intent.py.

Original contract:
    - Extends Strategy (StrategyBase)
    - Uses prepare_data() → entry_signal/exit_signal columns
    - NOT OrderIntent-based

This file is intentionally preserved so regression tests still pass.
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, Optional

import pandas as pd

from mantis_core.config import StrategyParams
from mantis_core.indicators import atr, rsi, sma
from mantis_core.strategies.base import Strategy

warnings.warn(
    "v050_trend_momentum uses the legacy StrategyBase contract. "
    "Migrate to IntentStrategy (v050_base_intent.py) for new work.",
    DeprecationWarning,
    stacklevel=2,
)


class V050TrendMomentum(Strategy):
    """v050_trend_momentum: Long Only Trend Following with RSI Momentum.

    LEGACY — Uses StrategyBase, not IntentStrategy.

    Logic:
      Entry: Close > SlowMA AND Close > FastMA AND RSI > rsi_entry
      Exit:  Close < FastMA OR RSI < rsi_exit
      Stop:  Fixed ATR stop (engine managed)
    """

    name = "v050_trend_momentum"

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
