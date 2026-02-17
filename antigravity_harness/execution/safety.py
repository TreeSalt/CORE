"""
safety.py — Execution Safety Guardrails
========================================
Pre-trade validation layer that wraps any ExecutionAdapter.
Enforces max position size, order rate limits, duplicate detection,
and calendar-aware trading cutoffs.
"""

from __future__ import annotations

import hashlib
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional, Set

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    ExecutionError,
    Fill,
    Order,
    OrderSide,
)


@dataclass
class SafetyConfig:
    """Configuration for execution safety guardrails."""
    max_position_size: float = 100.0
    max_notional_value: float = 1_000_000.0
    max_orders_per_minute: int = 60
    duplicate_window_seconds: float = 5.0
    enable_calendar_cutoff: bool = True


@dataclass
class SafetyTelemetry:
    """Telemetry counters for safety gate activity."""
    orders_submitted: int = 0
    orders_blocked_position: int = 0
    orders_blocked_rate: int = 0
    orders_blocked_duplicate: int = 0
    orders_blocked_calendar: int = 0
    orders_blocked_notional: int = 0


class ExecutionSafety:
    """
    Sovereign Safety Wrapper — Pre-Trade Guardrails.

    Wraps an ExecutionAdapter and enforces:
      1. Max position size per symbol
      2. Max notional value per order
      3. Order rate limiting (orders/minute)
      4. Duplicate order detection (fingerprint-based)
      5. Calendar-aware cutoff (no new positions after cutoff)

    All violations are fail-closed: order is REJECTED, not queued.
    """

    def __init__(
        self,
        adapter: ExecutionAdapter,
        config: Optional[SafetyConfig] = None,
        calendar: Any = None,
    ):
        self._adapter = adapter
        self._config = config or SafetyConfig()
        self._calendar = calendar

        # Rate limiting state
        self._order_timestamps: Deque[float] = deque()

        # Duplicate detection state
        self._recent_fingerprints: Dict[str, float] = {}

        # Telemetry
        self.telemetry = SafetyTelemetry()

    @property
    def config(self) -> SafetyConfig:
        return self._config

    def _order_fingerprint(self, order: Order) -> str:
        """Generate a deterministic fingerprint for duplicate detection."""
        raw = f"{order.symbol}|{order.side.value}|{order.qty}|{order.order_type.value}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _check_rate_limit(self) -> bool:
        """Check if order rate is within limits."""
        now = time.monotonic()
        cutoff = now - 60.0

        # Purge old timestamps
        while self._order_timestamps and self._order_timestamps[0] < cutoff:
            self._order_timestamps.popleft()

        return len(self._order_timestamps) < self._config.max_orders_per_minute

    def _check_duplicate(self, order: Order) -> bool:
        """Check if this order is a duplicate within the detection window."""
        fingerprint = self._order_fingerprint(order)
        now = time.monotonic()

        # Purge expired fingerprints
        expired: Set[str] = set()
        for fp, ts in self._recent_fingerprints.items():
            if now - ts > self._config.duplicate_window_seconds:
                expired.add(fp)
        for fp in expired:
            del self._recent_fingerprints[fp]

        if fingerprint in self._recent_fingerprints:
            return True  # Duplicate detected

        self._recent_fingerprints[fingerprint] = now
        return False

    def _check_position_limit(self, order: Order) -> bool:
        """Check if resulting position would exceed max size."""
        current = self._adapter.get_position(order.symbol)
        projected = current + order.qty if order.side == OrderSide.BUY else current - order.qty

        return abs(projected) <= self._config.max_position_size

    def _check_notional_limit(self, order: Order, reference_price: float) -> bool:
        """Check if order notional exceeds max allowed."""
        notional = order.qty * reference_price
        return notional <= self._config.max_notional_value

    def _check_calendar_cutoff(self, order: Order) -> bool:
        """Check if calendar says no new positions allowed."""
        if not self._config.enable_calendar_cutoff:
            return True
        if self._calendar is None:
            return True

        # Only block new position entries, not flattening exits
        if order.side == OrderSide.SELL:
            return True

        if order.timestamp is not None:
            return not self._calendar.no_new_positions_after(order.timestamp)

        return True

    def submit_order(
        self, order: Order, reference_price: Optional[float] = None
    ) -> Fill:
        """
        Submit an order through all safety gates.

        Raises ExecutionError if any gate blocks the order.
        """
        self.telemetry.orders_submitted += 1

        # Gate 1: Rate limit
        if not self._check_rate_limit():
            self.telemetry.orders_blocked_rate += 1
            raise ExecutionError(
                f"Rate limit exceeded ({self._config.max_orders_per_minute}/min)",
                order=order,
                reason="RATE_LIMIT",
            )

        # Gate 2: Duplicate detection
        if self._check_duplicate(order):
            self.telemetry.orders_blocked_duplicate += 1
            raise ExecutionError(
                f"Duplicate order detected for {order.symbol}",
                order=order,
                reason="DUPLICATE",
            )

        # Gate 3: Position size
        if not self._check_position_limit(order):
            self.telemetry.orders_blocked_position += 1
            raise ExecutionError(
                f"Position limit exceeded for {order.symbol} "
                f"(max: {self._config.max_position_size})",
                order=order,
                reason="POSITION_LIMIT",
            )

        # Gate 4: Notional limit
        if reference_price is not None and not self._check_notional_limit(order, reference_price):
            self.telemetry.orders_blocked_notional += 1
            raise ExecutionError(
                    f"Notional limit exceeded for {order.symbol} "
                    f"(max: {self._config.max_notional_value})",
                    order=order,
                    reason="NOTIONAL_LIMIT",
                )

        # Gate 5: Calendar cutoff
        if not self._check_calendar_cutoff(order):
            self.telemetry.orders_blocked_calendar += 1
            raise ExecutionError(
                "Calendar cutoff — no new positions after trading cutoff",
                order=order,
                reason="CALENDAR_CUTOFF",
            )

        # All gates passed — record timestamp and delegate
        self._order_timestamps.append(time.monotonic())
        return self._adapter.submit_order(order)

    def get_telemetry(self) -> Dict[str, Any]:
        """Return safety telemetry as a dictionary."""
        return {
            "orders_submitted": self.telemetry.orders_submitted,
            "orders_blocked_position": self.telemetry.orders_blocked_position,
            "orders_blocked_rate": self.telemetry.orders_blocked_rate,
            "orders_blocked_duplicate": self.telemetry.orders_blocked_duplicate,
            "orders_blocked_calendar": self.telemetry.orders_blocked_calendar,
            "orders_blocked_notional": self.telemetry.orders_blocked_notional,
        }
