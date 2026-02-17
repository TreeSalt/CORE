"""
antigravity_harness/execution/safety.py
=======================================
Execution Safety Layer — the last gate before any order reaches a broker.

Enforces operator hard limits from seed_profile. These are not suggestions.
Violations raise ExecutionSafetyError. Nothing can override them.

Layer order (from strategy to broker):
    Strategy → [Safety] → WAL → Compliance → Adapter

This module ONLY enforces per-trade and per-session hard limits.
Portfolio-level drawdown (SafetyOverlay) lives in portfolio_safety_overlay.py.

Does NOT: contain strategy logic, broker calls, or profile mutation.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from antigravity_harness.execution.adapter_base import (
    CalendarAdapter,
    ExecutionAdapter,
    Fill,
    OrderIntent,
    OrderSide,
    OrderType,
    Position,
)
from antigravity_harness.instruments.mes import (
    MES_DAILY_ATR_NO_TRADE,
    MES_DAILY_LOSS_CAP_USD,
    MES_MAX_CONTRACTS_PHASE1,
    MES_MAX_PLANNED_RISK_USD,
    MES_POINT_VALUE,
    MES_SLIPPAGE_BUFFER_TICKS,
    MES_STOP_POINTS,
    MES_TICK_VALUE,
)

logger = logging.getLogger("EXECUTION_SAFETY")


# ─── Errors ───────────────────────────────────────────────────────────────────


class ExecutionSafetyError(RuntimeError):
    """Raised when a hard safety limit would be violated. Order is NOT submitted."""
    pass


class DailyLossCapReached(ExecutionSafetyError):
    """Trading is paused for the session. Daily loss cap has been hit."""
    pass


class SessionBoundaryViolation(ExecutionSafetyError):
    """Order rejected: outside allowed trading window."""
    pass


class ATRFilterBlock(ExecutionSafetyError):
    """Order rejected: daily ATR exceeds no-trade threshold."""
    pass


class RiskLimitViolation(ExecutionSafetyError):
    """Order rejected: planned risk exceeds $40 hard limit."""
    pass


class ContractLimitViolation(ExecutionSafetyError):
    """Order rejected: would exceed max_contracts_phase1."""
    pass


# ─── Session State ────────────────────────────────────────────────────────────


@dataclass
class SessionState:
    """
    Mutable state for a single trading session.
    Reset at session open. Persisted to WAL for crash recovery.
    """
    session_date: date
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    trades_today: int = 0
    pause_trading: bool = False      # True after daily loss cap hit
    pause_reason: str = ""
    fills_today: list = field(default_factory=list)

    @property
    def total_pnl_usd(self) -> float:
        return self.realized_pnl_usd + self.unrealized_pnl_usd


# ─── Safety Config ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExecutionSafetyConfig:
    """
    Hard limits. All values must match seed_profile v1.0.1.
    Frozen — do not modify defaults without explicit profile update.
    """
    max_planned_risk_usd: float = MES_MAX_PLANNED_RISK_USD           # $40.00
    daily_loss_cap_usd: float = MES_DAILY_LOSS_CAP_USD               # $80.00
    max_contracts: int = MES_MAX_CONTRACTS_PHASE1                    # 1
    daily_atr_no_trade: float = MES_DAILY_ATR_NO_TRADE               # 80 pts
    stop_points: float = MES_STOP_POINTS                             # 7 pts
    slippage_buffer_ticks: int = MES_SLIPPAGE_BUFFER_TICKS           # 4 tks


# ─── Safety Layer ─────────────────────────────────────────────────────────────


class ExecutionSafety:
    """
    The last gate before any order reaches a broker.

    Usage:
        safety = ExecutionSafety(config, calendar)
        safety.new_session(today)

        # Before every order:
        safety.check_intent(intent, current_daily_atr, current_time_utc)

        # After every fill:
        safety.record_fill(fill)

        # After every bar (unrealized P&L update):
        safety.update_unrealized(pnl_usd)
    """

    def __init__(
        self,
        config: ExecutionSafetyConfig,
        calendar: CalendarAdapter,
    ) -> None:
        self.config = config
        self.calendar = calendar
        self._state: Optional[SessionState] = None

    def new_session(self, session_date: date) -> SessionState:
        """Call at session open to reset daily counters."""
        self._state = SessionState(session_date=session_date)
        logger.info(f"Safety: new session {session_date}")
        return self._state

    @property
    def state(self) -> SessionState:
        if self._state is None:
            raise RuntimeError("ExecutionSafety: call new_session() before trading.")
        return self._state

    # ── Gate 0: Pause Mode ────────────────────────────────────────────────────

    def _check_pause(self) -> None:
        if self.state.pause_trading:
            raise DailyLossCapReached(
                f"Trading PAUSED for session. Reason: {self.state.pause_reason}. "
                f"Realized P&L today: ${self.state.realized_pnl_usd:.2f}. "
                f"Total (incl. unrealized): ${self.state.total_pnl_usd:.2f}"
            )

    # ── Gate 1: Daily Loss Cap ─────────────────────────────────────────────────

    def _check_daily_loss(self) -> None:
        if self.state.total_pnl_usd <= -self.config.daily_loss_cap_usd:
            self.state.pause_trading = True
            self.state.pause_reason = (
                f"Daily loss cap hit: ${self.state.total_pnl_usd:.2f} <= "
                f"-${self.config.daily_loss_cap_usd:.2f}"
            )
            logger.critical(f"🛑 {self.state.pause_reason}")
            raise DailyLossCapReached(self.state.pause_reason)

    # ── Gate 2: ATR Filter ────────────────────────────────────────────────────

    def _check_atr(self, daily_atr_points: float) -> None:
        if daily_atr_points > self.config.daily_atr_no_trade:
            raise ATRFilterBlock(
                f"Daily ATR {daily_atr_points:.1f} pts exceeds "
                f"no-trade threshold {self.config.daily_atr_no_trade:.1f} pts. "
                f"An 8-point stop is statistically unreliable in this volatility."
            )

    # ── Gate 3: Session Boundary ──────────────────────────────────────────────

    def _check_session(self, now_utc: datetime) -> None:
        d = now_utc.date()
        if not self.calendar.is_trading_day(d):
            raise SessionBoundaryViolation(f"{d} is not a trading day.")

        no_new = self.calendar.no_new_positions_time_utc(d)
        if no_new and now_utc >= no_new:
            raise SessionBoundaryViolation(
                f"No new positions after {no_new.strftime('%H:%M')} UTC. "
                f"Current time: {now_utc.strftime('%H:%M')} UTC."
            )

    # ── Gate 4: Contract Limit ────────────────────────────────────────────────

    def _check_contracts(self, intent: OrderIntent, current_position: int) -> None:
        if abs(intent.quantity) > self.config.max_contracts:
            raise ContractLimitViolation(
                f"Intent requests {intent.quantity} contracts. "
                f"Hard limit: {self.config.max_contracts}."
            )
        # Would the resulting position exceed the limit?
        new_position = current_position + (
            intent.quantity if intent.side == OrderSide.BUY else -intent.quantity
        )
        if abs(new_position) > self.config.max_contracts:
            raise ContractLimitViolation(
                f"Order would result in position of {new_position} contracts. "
                f"Hard limit: {self.config.max_contracts}."
            )

    # ── Gate 5: Risk Math ─────────────────────────────────────────────────────

    def _check_risk(self, intent: OrderIntent) -> None:
        """
        Verify planned_stop_risk + buffer_risk <= $40.

        For limit/market entries: stop risk = stop_points × point_value × contracts
        For stop orders being used as exits: risk is already committed; skip this gate.
        """
        if intent.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
            # This is an exit order, not an entry. Risk already committed.
            return

        stop_risk = self.config.stop_points * MES_POINT_VALUE * intent.quantity
        buffer_risk = self.config.slippage_buffer_ticks * MES_TICK_VALUE * intent.quantity
        total_planned = stop_risk + buffer_risk

        if total_planned > self.config.max_planned_risk_usd:
            raise RiskLimitViolation(
                f"Planned risk ${total_planned:.2f} exceeds hard limit "
                f"${self.config.max_planned_risk_usd:.2f}. "
                f"stop=${stop_risk:.2f} + buffer=${buffer_risk:.2f}. "
                f"Reduce contracts or widen buffer tolerance."
            )

    # ── Public Gate Check ─────────────────────────────────────────────────────

    def check_intent(
        self,
        intent: OrderIntent,
        daily_atr_points: float,
        now_utc: datetime,
        current_position: int = 0,
    ) -> None:
        """
        Run all safety gates against an OrderIntent.

        Raises ExecutionSafetyError (or subclass) if any gate fails.
        Returns None (silently) if all gates pass.

        Call this BEFORE logging to WAL or submitting to broker.
        """
        self._check_pause()
        self._check_daily_loss()
        self._check_atr(daily_atr_points)
        self._check_session(now_utc)
        self._check_contracts(intent, current_position)
        self._check_risk(intent)
        logger.debug(f"Safety: intent approved [{intent.symbol} {intent.side.value} {intent.quantity}]")

    # ── Fill Recording ────────────────────────────────────────────────────────

    def record_fill(self, fill: Fill) -> None:
        """
        Update session state after a fill.
        Called by FillTape after every confirmed execution.
        """
        # P&L contribution from commission (cost)
        self.state.realized_pnl_usd -= fill.commission_usd
        self.state.trades_today += 1
        self.state.fills_today.append(fill)

        # Check if daily cap is now hit
        try:
            self._check_daily_loss()
        except DailyLossCapReached:
            pass  # Already logged and state.pause_trading set in _check_daily_loss

    def record_realized_pnl(self, pnl_usd: float) -> None:
        """Call when a position is closed to record realized P&L."""
        self.state.realized_pnl_usd += pnl_usd
        try:
            self._check_daily_loss()
        except DailyLossCapReached:
            pass

    def update_unrealized(self, unrealized_pnl_usd: float) -> None:
        """Update unrealized P&L (call on every bar tick)."""
        self.state.unrealized_pnl_usd = unrealized_pnl_usd
        if self.state.total_pnl_usd <= -self.config.daily_loss_cap_usd:
            if not self.state.pause_trading:
                self.state.pause_trading = True
                self.state.pause_reason = (
                    f"Daily loss cap hit on unrealized: "
                    f"${self.state.total_pnl_usd:.2f}"
                )
                logger.critical(f"🛑 {self.state.pause_reason}")
