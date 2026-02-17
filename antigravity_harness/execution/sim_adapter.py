"""
sim_adapter.py — Simulation Mode Execution Adapter
===================================================
Implements ExecutionAdapter for backtest/simulation mode.
Applies configurable slippage model and records all fills
to a FillTape for post-trade analysis.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    ExecutionError,
    Fill,
    Order,
    OrderSide,
)
from antigravity_harness.execution.fill_tape import FillTape


class SimAdapter(ExecutionAdapter):
    """
    Simulation Execution Adapter — Deterministic Fill Engine.

    Features:
      - Configurable slippage model (fixed bps)
      - Configurable commission model
      - Deterministic fills (no randomness)
      - All fills recorded to FillTape
      - Position tracking per symbol
    """

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        slippage_bps: float = 5.0,
        commission_per_unit: float = 0.0,
        commission_fixed: float = 0.0,
        fill_tape: Optional[FillTape] = None,
    ):
        self._cash = float(initial_cash)
        self._slippage_bps = slippage_bps
        self._commission_per_unit = commission_per_unit
        self._commission_fixed = commission_fixed
        self._positions: Dict[str, float] = {}
        self._fills: List[Fill] = []
        self._tape = fill_tape or FillTape()
        self._cancelled: set = set()

    @property
    def tape(self) -> FillTape:
        return self._tape

    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        """Apply slippage model to get fill price."""
        slip_frac = self._slippage_bps / 10000.0
        if side == OrderSide.BUY:
            return price * (1.0 + slip_frac)
        return price * (1.0 - slip_frac)

    def _compute_commission(self, qty: float) -> float:
        """Compute commission for a fill."""
        return (qty * self._commission_per_unit) + self._commission_fixed

    def submit_order(self, order: Order) -> Fill:
        """
        Execute an order deterministically with slippage and commission.

        Raises ExecutionError if:
          - Insufficient cash for buy
          - Insufficient position for sell
          - Zero or negative quantity
        """
        if order.qty <= 0:
            raise ExecutionError("Order quantity must be positive", order, "INVALID_QTY")

        # Determine reference price (use limit/stop if set, else use metadata)
        ref_price = order.metadata.get("reference_price", 0.0)
        if order.limit_price is not None:
            ref_price = order.limit_price
        elif order.stop_price is not None:
            ref_price = order.stop_price

        if ref_price <= 0:
            raise ExecutionError(
                "Reference price required (set via metadata['reference_price'] "
                "or limit_price/stop_price)",
                order, "NO_PRICE",
            )

        fill_price = self._apply_slippage(ref_price, order.side)
        commission = self._compute_commission(order.qty)
        slippage = fill_price - ref_price

        if order.side == OrderSide.BUY:
            total_cost = (order.qty * fill_price) + commission
            if total_cost > self._cash:
                raise ExecutionError(
                    f"Insufficient cash: need {total_cost:.2f}, "
                    f"have {self._cash:.2f}",
                    order, "INSUFFICIENT_CASH",
                )
            self._cash -= total_cost
            self._positions[order.symbol] = (
                self._positions.get(order.symbol, 0.0) + order.qty
            )
        else:
            current_pos = self._positions.get(order.symbol, 0.0)
            if order.qty > current_pos + 1e-9:
                raise ExecutionError(
                    f"Insufficient position: need {order.qty:.4f}, "
                    f"have {current_pos:.4f}",
                    order, "INSUFFICIENT_POSITION",
                )
            proceeds = (order.qty * fill_price) - commission
            self._cash += proceeds
            self._positions[order.symbol] = current_pos - order.qty
            if abs(self._positions[order.symbol]) < 1e-9:
                self._positions[order.symbol] = 0.0

        fill = Fill(
            order_id=order.order_id or str(uuid.uuid4())[:8],
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            fill_price=fill_price,
            expected_price=ref_price,
            slippage=slippage,
            commission=commission,
            timestamp=order.timestamp or datetime.utcnow(),
            metadata=order.metadata,
        )

        self._fills.append(fill)
        self._tape.record(fill)
        return fill

    def cancel_order(self, order_id: str) -> bool:
        """In sim mode, orders are always instant-fill, so cancel always fails."""
        self._cancelled.add(order_id)
        return False

    def get_fills(self, symbol: Optional[str] = None) -> List[Fill]:
        """Get fill history, optionally filtered by symbol."""
        if symbol is None:
            return list(self._fills)
        return [f for f in self._fills if f.symbol == symbol]

    def get_position(self, symbol: str) -> float:
        """Get current position for a symbol."""
        return self._positions.get(symbol, 0.0)

    def get_cash(self) -> float:
        """Get current cash balance."""
        return self._cash
