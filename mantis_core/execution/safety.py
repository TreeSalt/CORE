from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, List, Optional, Tuple

from mantis_core.execution.adapter_base import OrderIntent, OrderSide, OrderType
from mantis_core.execution.slippage import PhysicsViolationError

# ─── Exceptions ───────────────────────────────────────────────────────────────

class SafetyViolation(Exception):
    """Base class for all safety gate violations."""
    pass

class DailyLossCapReached(SafetyViolation):
    """Daily realized + unrealized loss exceeds the hard cap."""
    pass

class ATRFilterBlock(SafetyViolation):
    """Market volatility (ATR) is outside of safe operating range."""
    pass

class SessionBoundaryViolation(SafetyViolation):
    """Attempted to trade outside of allowed RTH or after cutoff."""
    pass

class ContractLimitViolation(SafetyViolation):
    """Order would exceed the maximum allowed position size."""
    pass

# ─── Configuration & State ────────────────────────────────────────────────────

@dataclass
class ExecutionSafetyConfig:
    daily_loss_cap_usd: float = 80.0
    atr_max_threshold: float = 80.0
    max_contracts: int = 1
    max_orders_per_sec: int = 5
    max_data_age_sec: float = 10.0

@dataclass
class ExecutionSafetyState:
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    pause_trading: bool = False
    pause_reason: str = ""
    last_session_date: Optional[date] = None

# ─── Execution Safety Engine ──────────────────────────────────────────────────

class ExecutionSafety:
    """
    Institutional Execution Safety Layer (Survival Mode).
    Combines static risk gates with active live execution circuit breakers.
    """
    def __init__(self, config: ExecutionSafetyConfig, calendar: Any):
        self.config = config
        self.calendar = calendar
        self.state = ExecutionSafetyState()
        self._order_timestamps: List[float] = []

    def new_session(self, current_date: date) -> None:
        """Reset session-specific state."""
        self.state.realized_pnl_usd = 0.0
        self.state.unrealized_pnl_usd = 0.0
        self.state.pause_trading = False
        self.state.pause_reason = ""
        self.state.last_session_date = current_date
        self._order_timestamps = []

    def update_unrealized(self, pnl_usd: float) -> None:
        """Update floating profit/loss for the daily cap check."""
        self.state.unrealized_pnl_usd = pnl_usd

    def check_intent(
        self,
        intent: OrderIntent,
        daily_atr_points: float,
        now_utc: datetime,
        current_position: int = 0
    ) -> None:
        """
        Run all safety gates. Raises SafetyViolation on failure.
        """
        self._check_pause_gate()
        self._check_daily_loss_gate()
        self._check_atr_gate(daily_atr_points)
        self._check_session_gate(now_utc)
        self._check_contract_limit_gate(intent, current_position)
        self._check_rapid_fire_gate()
        self._check_stale_data_gate(now_utc)

    def _check_pause_gate(self) -> None:
        if self.state.pause_trading:
            raise DailyLossCapReached(f"TRADING_PAUSED: {self.state.pause_reason}")

    def _check_daily_loss_gate(self) -> None:
        total_pnl = self.state.realized_pnl_usd + self.state.unrealized_pnl_usd
        if total_pnl <= -self.config.daily_loss_cap_usd:
            self.state.pause_trading = True
            self.state.pause_reason = f"Daily Loss Cap reached: ${total_pnl:.2f}"
            raise DailyLossCapReached(self.state.pause_reason)

    def _check_atr_gate(self, daily_atr_points: float) -> None:
        if daily_atr_points > self.config.atr_max_threshold:
            raise ATRFilterBlock(f"ATR {daily_atr_points} exceeds threshold {self.config.atr_max_threshold}")

    def _check_session_gate(self, now_utc: datetime) -> None:
        if self.calendar:
            d = now_utc.date()
            if not self.calendar.is_trading_day(d):
                raise SessionBoundaryViolation(f"Market closed on {d}")
            
            cutoff = self.calendar.no_new_positions_time_utc(d)
            if cutoff and now_utc > cutoff:
                raise SessionBoundaryViolation(f"After session entry cutoff: {now_utc} > {cutoff}")

    def _check_contract_limit_gate(self, intent: OrderIntent, current_position: int) -> None:
        # MISSION v4.5.290: Enforce integer lot physics
        if not isinstance(intent.quantity, int) or float(intent.quantity) != float(int(intent.quantity)):
             raise PhysicsViolationError(f"FRACTIONAL_ORDER: Contract quantity {intent.quantity} must be integer.")

        if intent.order_type != OrderType.STOP: # Exits skip limit check usually
            resulting_pos = current_position + (intent.quantity if intent.side == OrderSide.BUY else -intent.quantity)
            if abs(resulting_pos) > self.config.max_contracts:
                raise ContractLimitViolation(f"Resulting position {resulting_pos} exceeds limit {self.config.max_contracts}")

    def _check_rapid_fire_gate(self) -> None:
        now_ts = time.time()
        self._order_timestamps = [ts for ts in self._order_timestamps if now_ts - ts <= 1.0]
        if len(self._order_timestamps) >= self.config.max_orders_per_sec:
            raise SafetyViolation("RAPID_FIRE: Too many orders in last second")
        self._order_timestamps.append(now_ts)

    def _check_stale_data_gate(self, now_utc: datetime) -> None:
        if self.config.max_data_age_sec > 0:
            now_real = datetime.now(timezone.utc)
            if now_utc.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=timezone.utc)
            if (now_real - now_utc).total_seconds() < 86400: # 24h window
                age = (now_real - now_utc).total_seconds()
                if age > self.config.max_data_age_sec:
                    raise SafetyViolation(f"STALE_DATA: Market data is {age:.1f}s old")

    def validate_intent(self, intent: OrderIntent, current_equity: float, data_ts_utc: datetime) -> Tuple[bool, str]:
        """
        Compatibility shim for SovereignGuard interface.
        """
        try:
            self.check_intent(intent, 0.0, data_ts_utc)
            return True, "OK"
        except SafetyViolation as e:
            return False, str(e)
        except Exception as e:
            return False, f"UNKNOWN_ERROR: {e}"

# Compatibility Alias
ExecutionSovereignGuard = ExecutionSafety
