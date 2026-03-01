"""
antigravity_harness/execution/sim_adapter.py
============================================
SimExecutionAdapter — deterministic paper broker for tests and Stage 1 research.

No network calls. No broker library imports. Fully deterministic.
Used in CI/CD, unit tests, and any environment where a live broker is unavailable.

Capabilities:
    - Instant market order fills at specified price
    - No slippage by default (set sim_slippage_ticks to add synthetic slippage)
    - Full position and order tracking
    - Commission deducted per fill

Does NOT: call any broker API. Does NOT import ib_insync, rithmic, or tradovate.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from antigravity_harness.config import DarkPoolModel, LatencyModel
from antigravity_harness.execution.adapter_base import (
    AdapterCapabilities,
    ExecutionAdapter,
    Fill,
    OrderAck,
    OrderIntent,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)
from antigravity_harness.execution.fill_tape import FillTape
from antigravity_harness.execution.slippage import PhysicsViolationError, apply_mes_friction
from antigravity_harness.instruments.mes import (
    MES_POINT_VALUE,
    MES_TICK_SIZE,
)


@dataclass
class _SimOrder:
    ack: OrderAck
    intent: OrderIntent
    status: OrderStatus = OrderStatus.SUBMITTED


class SimExecutionAdapter(ExecutionAdapter):
    """
    Deterministic simulation adapter. Fills market orders immediately.
    Use for unit tests, CI, and Stage 1 research environments.

    Usage:
        adapter = SimExecutionAdapter(initial_cash=2000.0, commission_per_rt=0.85)
        await adapter.connect()
        ack = await adapter.submit_order(intent)
        # check fill tape...
    """

    def __init__(
        self,
        initial_cash: float = 2000.0,
        commission_per_rt: float = 0.85,
        sim_slippage_ticks: int = 0,
        latency_model: Optional[LatencyModel] = None,
        dark_pool_model: Optional[DarkPoolModel] = None,
        fill_tape: Optional[FillTape] = None,
        paper: bool = True,
    ) -> None:
        self._cash = initial_cash
        self._commission_per_rt = commission_per_rt
        self._sim_slippage_ticks = sim_slippage_ticks
        self._latency_model = latency_model or LatencyModel()
        self._dark_pool_model = dark_pool_model or DarkPoolModel()
        self._fill_tape = fill_tape
        self._paper = paper
        self._positions: dict[str, int] = {}        # symbol → qty
        self._avg_costs: dict[str, float] = {}      # symbol → avg cost
        self._open_orders: dict[str, _SimOrder] = {}
        self._fills: List[Fill] = []
        self._realized_pnl: float = 0.0
        self._connected = False
        self._current_prices: dict[str, float] = {}  # set externally for unrealized P&L
        self._current_volumes: dict[str, float] = {}
        self._current_vols: dict[str, float] = {}

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_server_side_brackets=False,
            supports_oco=False,
            supports_cancel_replace=False,
            supports_order_status_push=False,
            supports_real_time_bars=False,
            supports_historical_bars=False,
            supports_paper_mode=True,
            supports_rollover_query=False,
        )

    @property
    def is_paper(self) -> bool:
        return self._paper

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    def set_price(self, symbol: str, price: float, volume: float = 0.0, volatility: float = 0.0) -> None:  # noqa: PLR0913
        """Set the current price, volume, and volatility for a symbol."""
        self._current_prices[symbol] = price
        self._current_volumes[symbol] = volume
        self._current_vols[symbol] = volatility

    async def get_position(self, symbol: str) -> Position:
        qty = self._positions.get(symbol, 0)
        avg_cost = self._avg_costs.get(symbol, 0.0)
        current = self._current_prices.get(symbol, avg_cost)
        unrealized = 0.0 if qty == 0 else (current - avg_cost) * MES_POINT_VALUE * qty
        return Position(
            symbol=symbol,
            quantity=qty,
            average_cost=Decimal(str(avg_cost)),
            unrealized_pnl_usd=unrealized,
            realized_pnl_today_usd=self._realized_pnl,
        )

    async def get_all_positions(self) -> List[Position]:
        return [
            await self.get_position(sym)
            for sym, qty in self._positions.items()
            if qty != 0
        ]

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderAck]:
        orders = [
            o.ack for o in self._open_orders.values()
            if o.status == OrderStatus.SUBMITTED
        ]
        if symbol:
            orders = [o for o in orders if o.client_order_id.startswith(symbol) or True]
        return orders

    async def submit_order(self, intent: OrderIntent) -> OrderAck:
        broker_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        ack = OrderAck(
            broker_order_id=broker_id,
            client_order_id=intent.client_order_id or broker_id,
            status=OrderStatus.SUBMITTED,
            submitted_at_utc=now,
        )

        order = _SimOrder(ack=ack, intent=intent)
        self._open_orders[broker_id] = order

        # Capture expected price at submission time (mid price)
        expected_price = self._current_prices.get(intent.symbol)

        # Market orders fill immediately (after optional delay)
        if intent.order_type == OrderType.MARKET:
            delay_ms = self._calculate_dynamic_delay(intent)
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
            
            fill = await self._fill_market_order(order)
            
            # Record in FillTape if available
            if self._fill_tape:
                self._fill_tape.record(fill, expected_price=expected_price)

        return ack

    async def _fill_market_order(self, order: _SimOrder) -> Fill:  # noqa: PLR0912, PLR0915
        intent = order.intent
        symbol = intent.symbol
        base_price = self._current_prices.get(symbol, 5000.0)
        dp = self._dark_pool_model
        commission = self._commission_per_rt * intent.quantity
        now = datetime.now(tz=timezone.utc)
        
        if not isinstance(intent.quantity, int) or float(intent.quantity) != float(int(intent.quantity)):
             raise PhysicsViolationError(f"FRACTIONAL_ORDER: {intent.quantity} contracts not allowed.")

        fill_price, commission = apply_mes_friction(base_price, intent.side, intent.quantity)
        
        # Add synthetic test slippage if requested
        if self._sim_slippage_ticks > 0:
            extra_slip = self._sim_slippage_ticks * MES_TICK_SIZE
            if intent.side == OrderSide.BUY:
                fill_price = Decimal(str(float(fill_price) + extra_slip))
            else:
                fill_price = Decimal(str(float(fill_price) - extra_slip))

        # Dark Pool Routing Logic (Hydra v2.4.1)
        exec_venue = "LIT_EXCHANGE"
        if dp.enabled:
            # Check for failure (fail_prob)
            if random.random() < dp.fail_prob:
                exec_venue = "LIT_EXCHANGE"
            else:
                # Potential Improvement
                exec_venue = "DARK_POOL"
                if random.random() < dp.improvement_prob:
                    improvement = float(fill_price) * (dp.improvement_bps / 10000.0)
                    if intent.side == OrderSide.BUY:
                        fill_price = Decimal(str(float(fill_price) - improvement))
                    else:
                        fill_price = Decimal(str(float(fill_price) + improvement))
                
                # Adverse Selection check
                if random.random() < dp.adverse_selection_prob:
                    slip = float(fill_price) * (dp.adverse_selection_bps / 10000.0)
                    if intent.side == OrderSide.BUY:
                        fill_price = Decimal(str(float(fill_price) + slip))
                    else:
                        fill_price = Decimal(str(float(fill_price) - slip))

        fill = Fill(
            broker_order_id=order.ack.broker_order_id,
            client_order_id=order.ack.client_order_id,
            symbol=symbol,
            side=intent.side,
            filled_qty=intent.quantity,
            fill_price=Decimal(str(round(fill_price, 2))),
            fill_time_utc=now,
            commission_usd=commission,
            venue=exec_venue,
        )

        self._fills.append(fill)
        order.status = OrderStatus.FILLED
        order.ack.status = OrderStatus.FILLED

        fill_price_f = float(fill_price)

        # Update position
        qty_delta = intent.quantity if intent.side == OrderSide.BUY else -intent.quantity
        prev_qty = self._positions.get(symbol, 0)
        new_qty = prev_qty + qty_delta
        self._positions[symbol] = new_qty

        # Update average cost (simplified — full FIFO accounting out of scope here)
        if new_qty == 0:
            realized = (fill_price_f - self._avg_costs.get(symbol, fill_price_f)) * MES_POINT_VALUE * abs(qty_delta)
            if prev_qty < 0:
                realized = -realized
            self._realized_pnl += realized - commission
            self._avg_costs[symbol] = 0.0
        elif prev_qty == 0:
            self._avg_costs[symbol] = fill_price_f
        else:
            _cost = self._avg_costs.get(symbol, fill_price_f)
            self._avg_costs[symbol] = (
                (_cost * abs(prev_qty) + fill_price_f * intent.quantity)
                / abs(new_qty)
            )

        return fill

    def _calculate_dynamic_delay(self, intent: OrderIntent) -> float:
        """Item 14: Dynamic latency calculation based on model settings."""
        if not self._latency_model:
            return 0.0
            
        delay = self._latency_model.base_ms
        
        # 1. Volatility Scaling
        symbol = intent.symbol
        vol = self._current_vols.get(symbol, 0.0)
        delay += vol * self._latency_model.vol_scaling_ms
        
        # 2. Size Scaling (Order Qty / Bar Volume)
        volume = self._current_volumes.get(symbol, 0.0)
        if volume > 0:
            size_impact = (intent.quantity / volume) * self._latency_model.size_scaling_ms
            delay += size_impact
            
        return delay

    async def cancel_order(self, broker_order_id: str) -> bool:
        if broker_order_id in self._open_orders:
            order = self._open_orders[broker_order_id]
            if order.status == OrderStatus.SUBMITTED:
                order.status = OrderStatus.CANCELLED
                order.ack.status = OrderStatus.CANCELLED
                return True
        return False

    async def get_account_cash(self) -> float:
        return self._cash

    async def get_realized_pnl_today(self) -> float:
        return self._realized_pnl

    @property
    def all_fills(self) -> List[Fill]:
        return list(self._fills)
