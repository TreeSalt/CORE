---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import typing

class CircuitBreaker:
    def __init__(self):
        self._tripped = False

    def check(self, state: dict) -> bool:
        if self._tripped:
            return False
        return True

    def trip(self, reason: str):
        self._tripped = True
        self._trip_reason = reason

    def reset(self, sovereign_signature: str):
        self._tripped = False


class DrawdownBreaker(CircuitBreaker):
    def __init__(self, max_drawdown_percent: float = 0.10):
        super().__init__()
        self.max_drawdown_percent = max_drawdown_percent

    def check(self, state: dict) -> bool:
        if not super().check(state):
            return False
        
        equity = state.get('equity')
        peak_equity = state.get('peak_equity')
        
        if equity is None or peak_equity is None:
            return True
            
        current_drawdown = (peak_equity - equity) / peak_equity
        return current_drawdown <= self.max_drawdown_percent


class DailyLossBreaker(CircuitBreaker):
    def __init__(self, max_daily_loss: float = 0.0):
        super().__init__()
        self.max_daily_loss = max_daily_loss

    def check(self, state: dict) -> bool:
        if not super().check(state):
            return False
        
        daily_loss = state.get('daily_loss', 0.0)
        return daily_loss <= self.max_daily_loss


class PositionConcentrationBreaker(CircuitBreaker):
    def __init__(self, max_concentration: float = 0.10):
        super().__init__()
        self.max_concentration = max_concentration

    def check(self, state: dict) -> bool:
        if not super().check(state):
            return False
        
        concentration = state.get('concentration', 0.0)
        return concentration <= self.max_concentration