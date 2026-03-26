---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import math
from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def init_params(self, config):
        """Initialize strategy parameters with a configuration dict."""
        pass

    @abstractmethod
    def on_bar(self, candle):
        """Process incoming market bar/candle data."""
        pass

    @abstractmethod
    def get_signal(self):
        """Calculate current trading signal (e.g., 1 for buy, -1 for sell, 0 for none)."""
        pass

    @abstractmethod
    def get_state(self):
        """Retrieve or update strategy state information."""
        pass

    def position_size(self, equity: float, risk_pct: float) -> float:
        """
        Calculate optimal position size based on Kelly-inspired logic.
        Uses fractional Kelly to mitigate overfitting and reduce variance.
        Assumes standard risk/reward dynamics where we manage % of equity at risk.
        """
        if equity <= 0 or risk_pct <= 0:
            return 0.0
        
        # Fractional Kelly factor (commonly 0.25 to 0.5) for base safety
        fraction = 0.5  
        
        # Simple Kelly-inspired sizing: Risk % of Equity * Fraction
        # In a full implementation, risk_pct would be the calculated kelly f * margin of safety
        max_risk_value = equity * (risk_pct / 100)
        return max_risk_value * fraction

    def should_enter(self, signal: float, regime: str) -> bool:
        """
        Determines if we should enter a trade based on signal and market regime.
        Blocks entry if signal is neutral/bad or regime is unfavorable (e.g., ranging/high vol).
        """
        if signal > 0.5:
            # Favorable regimes for long entries
            return regime in ['bullish', 'neutral'] or regime == 'high_vol'
        elif signal < -0.5:
            # Favorable regimes for short entries
            return regime in ['bearish', 'neutral'] or regime == 'high_vol'
        
        return False

    def should_exit(self, position, candle, stop_loss: float, take_profit: float) -> bool:
        """
        Determines if a trade should be exited based on price action against SL/TP.
        Assumes position dict contains 'side' ('long' or 'short') for logic adjustment.
        """
        current_price = candle.get('close', 0)
        
        # Determine direction from position state to handle Long vs Short exit logic
        side = getattr(position, 'side', getattr(position, 'get', lambda: None)('side', 'long')) or 'long'
        
        if side == 'long':
            return current_price >= take_profit or current_price <= stop_loss
        else:  # short
            return current_price <= take_profit or current_price >= stop_loss
        
        return False