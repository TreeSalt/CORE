"""
antigravity_harness/execution/fiduciary.py
=========================================
Fiduciary Bridge — a protective wrapper for execution adapters.
Enforces strict micro-sizing limits (fiduciary clamping) to prevent 
unauthorized risk exposure in live or paper environments.
"""

import logging
from dataclasses import replace
from typing import List, Optional

from mantis_core.execution.adapter_base import (
    AdapterCapabilities,
    ExecutionAdapter,
    OrderAck,
    OrderIntent,
    Position,
)

logger = logging.getLogger("FIDUCIARY")

class FiduciaryBridge(ExecutionAdapter):
    """
    Wraps an existing ExecutionAdapter and clamps order quantities to 
    fiduciary limits. This is a fail-safe against strategy-layer errors
    that might propose excessive size in real markets.
    """

    def __init__(self, base_adapter: ExecutionAdapter, max_qty: int = 1):
        self._base = base_adapter
        self._max_qty = max_qty
        logger.info(f"Fiduciary Bridge enabled: max_qty={max_qty}")

    @property
    def capabilities(self) -> AdapterCapabilities:
        return self._base.capabilities

    @property
    def is_paper(self) -> bool:
        return self._base.is_paper

    async def connect(self) -> None:
        await self._base.connect()

    async def disconnect(self) -> None:
        await self._base.disconnect()

    async def get_position(self, symbol: str) -> Position:
        return await self._base.get_position(symbol)

    async def get_all_positions(self) -> List[Position]:
        return await self._base.get_all_positions()

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderAck]:
        return await self._base.get_open_orders(symbol)

    async def submit_order(self, intent: OrderIntent) -> OrderAck:
        """
        Intercept order submission and enforce fiduciary quantity clamping.
        """
        if intent.quantity > self._max_qty:
            logger.warning(
                f"🛡️ FIDUCIARY CLAMP: Intent {intent.symbol} qty {intent.quantity} "
                f"exceeds limit {self._max_qty}. Clamping to {self._max_qty}."
            )
            # Use replace to maintain immutability of OrderIntent
            intent = replace(intent, quantity=self._max_qty)

        return await self._base.submit_order(intent)

    async def cancel_order(self, broker_order_id: str) -> bool:
        return await self._base.cancel_order(broker_order_id)

    async def get_account_cash(self) -> float:
        return await self._base.get_account_cash()

    async def get_realized_pnl_today(self) -> float:
        return await self._base.get_realized_pnl_today()
