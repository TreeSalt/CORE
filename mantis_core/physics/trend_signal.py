import numpy as np
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


class SignalAction(Enum):
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT = "EXIT"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True)
class TradeSignal:
    action: SignalAction
    strength: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    timestamp: datetime


class TrendSignalGenerator:
    def __init__(
        self,
        ema_fast_period: int = 20,
        ema_slow_period: int = 50,
        atr_stop_multiplier: float = 2.0,
        atr_target_multiplier: float = 3.0
    ):
        self.ema_fast_period = ema_fast_period
        self.ema_slow_period = ema_slow_period
        self.atr_stop_multiplier = atr_stop_multiplier
        self.atr_target_multiplier = atr_target_multiplier

    def _compute_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        alpha = 2.0 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
        return ema

    def generate_signal(
        self,
        closes: np.ndarray,
        current_price: float,
        regime: str,
        atr: float
    ) -> TradeSignal:
        if len(closes) < self.ema_slow_period:
            raise ValueError(f"closes array must have at least {self.ema_slow_period} elements")

        if current_price <= 0:
            raise ValueError("current_price must be positive")

        for price in closes:
            if price <= 0:
                raise ValueError("All close prices must be positive")

        fast_ema = self._compute_ema(closes, self.ema_fast_period)
        slow_ema = self._compute_ema(closes, self.ema_slow_period)

        current_fast_ema = fast_ema[-1]
        current_slow_ema = slow_ema[-1]

        non_trending_regimes = {"RANGING", "VOLATILE", "UNKNOWN"}
        if regime in non_trending_regimes:
            return TradeSignal(
                action=SignalAction.NO_ACTION,
                strength=0.0,
                entry_price=None,
                stop_loss=None,
                take_profit=None,
                reasoning=f"Regime {regime} is not a trending market",
                timestamp=datetime.now(timezone.utc)
            )

        if regime == "TRENDING_UP":
            if current_fast_ema > current_slow_ema and current_price > current_fast_ema:
                strength = abs(current_fast_ema - current_slow_ema) / current_price
                strength = max(0.0, min(1.0, strength))
                stop_loss = current_price - (atr * self.atr_stop_multiplier)
                take_profit = current_price + (atr * self.atr_target_multiplier)
                return TradeSignal(
                    action=SignalAction.ENTER_LONG,
                    strength=strength,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning="Trending up with bullish EMA crossover confirmed",
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                return TradeSignal(
                    action=SignalAction.NO_ACTION,
                    strength=0.0,
                    entry_price=None,
                    stop_loss=None,
                    take_profit=None,
                    reasoning="TRENDING_UP but entry conditions not met",
                    timestamp=datetime.now(timezone.utc)
                )

        if regime == "TRENDING_DOWN":
            if current_fast_ema < current_slow_ema and current_price < current_fast_ema:
                strength = abs(current_fast_ema - current_slow_ema) / current_price
                strength = max(0.0, min(1.0, strength))
                stop_loss = current_price + (atr * self.atr_stop_multiplier)
                take_profit = current_price - (atr * self.atr_target_multiplier)
                return TradeSignal(
                    action=SignalAction.ENTER_SHORT,
                    strength=strength,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning="Trending down with bearish EMA crossover confirmed",
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                return TradeSignal(
                    action=SignalAction.NO_ACTION,
                    strength=0.0,
                    entry_price=None,
                    stop_loss=None,
                    take_profit=None,
                    reasoning="TRENDING_DOWN but entry conditions not met",
                    timestamp=datetime.now(timezone.utc)
                )

        return TradeSignal(
            action=SignalAction.NO_ACTION,
            strength=0.0,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            reasoning=f"Unknown regime type: {regime}",
            timestamp=datetime.now(timezone.utc)
        )
