"""
antigravity_harness/strategies/v050_base_intent.py
===================================================
v050 Strategy Architecture — OrderIntent-Only Skeleton.

All v050+ strategies output OrderIntent objects, NOT broker calls.
The strategy layer is completely isolated from execution layer.

Architecture:
    Strategy.generate_intent(bar_data) → Optional[OrderIntent]
    Safety.check_intent(intent) → None or raise
    WAL.log_intent(intent)
    Compliance.vet_intent(intent)
    Adapter.submit_order(intent) → Fill

Strategies in this generation:
    - Cannot import any execution module
    - Cannot import any broker library
    - Cannot call any network resource
    - May only use: bar data, indicators, instruments constants, profiles

Does NOT: submit orders, call brokers, or contain safety logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from antigravity_harness.execution.adapter_base import (
    OrderIntent,
    OrderSide,
    OrderType,
    TimeInForce,
)
from antigravity_harness.instruments.mes import (
    MES_CONTRACT_SYMBOL,
    MESRiskParams,
)

# ─── Intent-Only Strategy Contract ───────────────────────────────────────────


@dataclass(frozen=True)
class StrategySignal:
    """
    The output of a v050+ strategy. Contains the desired trade direction
    and all information needed to construct an OrderIntent.

    Does NOT contain broker fields.
    Does NOT contain risk management (safety layer handles that).
    """
    direction: str             # "LONG" or "SHORT" or "FLAT"
    entry_bar_close: float     # Close price of the signal bar (for reference)
    signal_time_utc: datetime  # When the signal was generated
    signal_source: str         # Strategy name for audit trail
    reason: str = ""           # Human-readable explanation


class IntentStrategy(ABC):
    """
    Base class for all v050+ strategies.

    Contract:
        - Implement generate_signal() to produce a StrategySignal
        - Never import execution modules
        - Never import broker libraries
        - All parameters from StrategyParams (config layer)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier. Used in audit trails."""
        ...

    @abstractmethod
    def generate_signal(
        self,
        bars: pd.DataFrame,
        risk_params: MESRiskParams,
        as_of: datetime,
    ) -> Optional[StrategySignal]:
        """
        Analyze bar data and return a StrategySignal if conditions are met.

        Args:
            bars: OHLCV DataFrame from DataTape. Index = datetime. Must be RTH only.
            risk_params: Frozen risk parameters (stop, buffer, max_contracts).
            as_of: The current bar's close time (anti-lookahead anchor).

        Returns:
            StrategySignal if entry conditions met, None if no signal.
        """
        ...

    def signal_to_intent(
        self,
        signal: StrategySignal,
        client_order_id: str,
    ) -> OrderIntent:
        """
        Convert a StrategySignal to an OrderIntent.
        Called by the engine AFTER safety checks pass.

        The strategy proposes the direction.
        Safety enforces the limits.
        The adapter executes.
        """
        side = OrderSide.BUY if signal.direction == "LONG" else OrderSide.SELL
        return OrderIntent(
            symbol=MES_CONTRACT_SYMBOL,
            side=side,
            quantity=1,  # Safety layer enforces max_contracts; strategy always proposes 1
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            client_order_id=client_order_id,
        )


# ─── v050 Skeleton: Trend-Pullback Intent Strategy ────────────────────────────


class V050TrendPullbackIntent(IntentStrategy):
    """
    v050 Trend-Pullback Strategy (Intent-only skeleton).

    Logic:
        LONG signal when:
            - Close > SMA(sma_period) — in uptrend
            - RSI(rsi_period) < rsi_oversold — pullback into trend
            - Daily ATR check delegated to safety layer

    This class generates signals only.
    Risk management is handled by ExecutionSafety.
    Order submission is handled by IBKRAdapter (or SimExecutionAdapter in tests).

    NOTE: This is the scaffold. Backtest validation on real MES DataTape
    required before paper trading. See Promotion Ladder Stage 1.
    """

    name = "v050_trend_pullback_intent"

    def __init__(
        self,
        sma_period: int = 50,
        rsi_period: int = 3,
        rsi_oversold: float = 20.0,
        rsi_overbought: float = 80.0,
    ) -> None:
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signal(
        self,
        bars: pd.DataFrame,
        risk_params: MESRiskParams,
        as_of: datetime,
    ) -> Optional[StrategySignal]:
        """
        Generate a LONG signal if trend + pullback conditions are met.

        Uses only bars up to and including `as_of` bar close (anti-lookahead).
        Returns None if insufficient data or conditions not met.
        """
        required_bars = max(self.sma_period, self.rsi_period + 1) + 1
        if len(bars) < required_bars:
            return None

        # Use only bars up to as_of (anti-lookahead enforcement)
        eligible = bars[bars.index <= as_of]
        if len(eligible) < required_bars:
            return None

        closes = eligible["Close"]
        current_close = closes.iloc[-1]

        # Trend filter: Close > SMA
        sma = closes.rolling(self.sma_period).mean().iloc[-1]
        if pd.isna(sma) or current_close <= sma:
            return None

        # RSI pullback: RSI < oversold threshold
        rsi = self._compute_rsi(closes, self.rsi_period)
        if pd.isna(rsi) or rsi >= self.rsi_oversold:
            return None

        return StrategySignal(
            direction="LONG",
            entry_bar_close=float(current_close),
            signal_time_utc=as_of,
            signal_source=self.name,
            reason=f"Close({current_close:.2f}) > SMA{self.sma_period}({sma:.2f}) AND RSI{self.rsi_period}({rsi:.1f}) < {self.rsi_oversold}",
        )

    def _compute_rsi(self, closes: pd.Series, period: int) -> float:
        """Compute RSI using Wilder's smoothing (standard)."""
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean().iloc[-1]
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
