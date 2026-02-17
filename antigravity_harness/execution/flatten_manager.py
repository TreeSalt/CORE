"""
flatten_manager.py — Widowmaker Fix: Mandatory Session Flattening
=================================================================
Handles end-of-session mandatory position flattening.
Integrates with CalendarAdapter.should_flatten() to determine
when to force-close all positions before session close.

The "Widowmaker Fix" ensures no positions are carried through
illiquid periods (e.g., overnight, over-weekend) where slippage
risk is catastrophic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    Fill,
    Order,
    OrderSide,
    OrderType,
)

logger = logging.getLogger(__name__)


@dataclass
class FlattenEvent:
    """Telemetry record for a flatten operation."""
    timestamp: datetime
    symbol: str
    qty_flattened: float
    fill_price: float
    slippage_bps: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FlattenManager:
    """
    Widowmaker Fix — Mandatory Session Flattening.

    Monitors the calendar and forces all open positions flat
    when the trading session is approaching close. This prevents
    carrying positions through illiquid overnight/weekend gaps.

    Flow:
      1. On each bar/tick, call `check_and_flatten(timestamp)`
      2. If `calendar.should_flatten(timestamp)` returns True, all
         open positions are closed via market orders
      3. Every flatten operation is logged to the event tape
    """

    def __init__(
        self,
        adapter: ExecutionAdapter,
        calendar: Any = None,
        on_flatten: Optional[Callable[[FlattenEvent], None]] = None,
    ):
        self._adapter = adapter
        self._calendar = calendar
        self._on_flatten = on_flatten
        self._events: List[FlattenEvent] = []
        self._flatten_count = 0

    @property
    def events(self) -> List[FlattenEvent]:
        """Immutable view of flatten event history."""
        return list(self._events)

    @property
    def flatten_count(self) -> int:
        return self._flatten_count

    def check_and_flatten(
        self,
        timestamp: datetime,
        symbols: List[str],
        reference_prices: Optional[Dict[str, float]] = None,
    ) -> List[Fill]:
        """
        Check calendar and flatten all positions if required.

        Args:
            timestamp: Current bar/tick timestamp
            symbols: List of symbols to check for open positions
            reference_prices: Optional map of symbol → current price
                              (used for slippage telemetry)

        Returns:
            List of fills from flatten orders (empty if no flattening needed)
        """
        if self._calendar is None:
            return []

        if not self._calendar.should_flatten(timestamp):
            return []

        logger.info("🔥 Widowmaker Flatten triggered at %s", timestamp)
        fills: List[Fill] = []

        for symbol in symbols:
            position = self._adapter.get_position(symbol)
            if abs(position) < 1e-9:
                continue

            # Determine side: if long, sell; if short, buy
            side = OrderSide.SELL if position > 0 else OrderSide.BUY
            qty = abs(position)

            ref_price = (reference_prices or {}).get(symbol, 0.0)

            order = Order(
                order_id=f"FLATTEN-{symbol}-{self._flatten_count}",
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=OrderType.MARKET,
                timestamp=timestamp,
                metadata={
                    "reason": "widowmaker_flatten",
                    "trigger": str(timestamp),
                    "reference_price": ref_price,
                },
            )

            try:
                fill = self._adapter.submit_order(order)
                fills.append(fill)

                event = FlattenEvent(
                    timestamp=timestamp,
                    symbol=symbol,
                    qty_flattened=qty,
                    fill_price=fill.fill_price,
                    slippage_bps=fill.slippage_bps,
                    reason="widowmaker_flatten",
                    metadata={"order_id": order.order_id},
                )
                self._events.append(event)
                self._flatten_count += 1

                if self._on_flatten:
                    self._on_flatten(event)

                logger.info(
                    "  Flattened %s: %.4f @ %.2f (slippage: %.1f bps)",
                    symbol, qty, fill.fill_price, fill.slippage_bps,
                )

            except Exception as e:
                logger.error(
                    "⛔ Flatten FAILED for %s: %s — POSITION STILL OPEN",
                    symbol, e,
                )
                # Fail-open for flatten: log error but don't crash
                # The position remains open, which is dangerous
                # but crashing during flatten is worse

        return fills

    def get_telemetry(self) -> Dict[str, Any]:
        """Return flatten telemetry summary."""
        total_slippage = sum(e.slippage_bps for e in self._events)
        avg_slippage = total_slippage / len(self._events) if self._events else 0.0

        return {
            "flatten_count": self._flatten_count,
            "total_events": len(self._events),
            "avg_slippage_bps": round(avg_slippage, 2),
            "symbols_flattened": list({e.symbol for e in self._events}),
        }
