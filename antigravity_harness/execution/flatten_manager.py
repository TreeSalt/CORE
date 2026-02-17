"""
antigravity_harness/execution/flatten_manager.py
================================================
FlattenManager — the "Widowmaker Fix."

Ensures clean position exit at session close or on safety trigger.
Handles the double-fill race condition that can accidentally reverse a position.

Protocol: "Close then Cancel"
    1. If position != 0: submit market close order first.
    2. Wait for position == 0 (verification loop, timeout).
    3. Then cancel all remaining open orders.
    4. Final verify: position == 0 AND open_orders == 0.
    5. If accidental reversal detected (double-fill race): immediately close the reversal.

Why "Close then Cancel" (not Cancel then Close):
    If you cancel a bracket's stop/target BEFORE closing the position,
    you are momentarily exposed without any protective order.
    Close the position first, then clean up the orders.

Does NOT: contain strategy logic or broker-specific code.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    OrderIntent,
    OrderSide,
    OrderType,
    Position,
    TimeInForce,
)

logger = logging.getLogger("FLATTEN_MANAGER")

# Tuning constants
VERIFY_POLL_INTERVAL_SEC: float = 0.5
VERIFY_TIMEOUT_SEC: float = 30.0
MAX_REVERSAL_CLOSE_ATTEMPTS: int = 3


# ─── Result Types ──────────────────────────────────────────────────────────────


@dataclass
class FlattenResult:
    """Outcome of a flatten operation."""
    success: bool
    symbol: str
    initial_position: int              # Position before flatten started
    final_position: int                # Should be 0 if success
    orders_cancelled: int
    reversal_detected: bool = False    # True if double-fill race occurred
    reversal_closed: bool = False      # True if reversal was auto-closed
    elapsed_sec: float = 0.0
    error: Optional[str] = None


# ─── FlattenManager ───────────────────────────────────────────────────────────


class FlattenManager:
    """
    Manages clean position exit for a single instrument.

    Usage:
        fm = FlattenManager(adapter)
        result = await fm.flatten("MES", reason="SESSION_CLOSE")

    Always await the result and check result.success.
    If result.success is False, escalate — do not leave a live position unattended.
    """

    def __init__(
        self,
        adapter: ExecutionAdapter,
        poll_interval_sec: float = VERIFY_POLL_INTERVAL_SEC,
        timeout_sec: float = VERIFY_TIMEOUT_SEC,
    ) -> None:
        self.adapter = adapter
        self.poll_interval = poll_interval_sec
        self.timeout = timeout_sec

    async def flatten(self, symbol: str, reason: str = "UNSPECIFIED") -> FlattenResult:
        """
        Flatten all positions and cancel all orders for symbol.

        Steps:
            1. Read current position.
            2. If position != 0: submit market close order.
            3. Poll until position == 0 OR timeout.
            4. Cancel all open orders.
            5. Verify: position == 0 AND open_orders == 0.
            6. If double-fill race created a reversal: close it.

        Returns FlattenResult. Always logs. Never raises (catches all exceptions
        so the caller can decide how to escalate a failed flatten).
        """
        logger.warning(f"FLATTEN initiated: {symbol} | reason={reason}")
        started_at = datetime.now(tz=timezone.utc)
        orders_cancelled = 0
        reversal_detected = False
        reversal_closed = False

        try:
            # ── Step 1: Read current position ─────────────────────────────────
            position = await self.adapter.get_position(symbol)
            initial_qty = position.quantity
            logger.info(f"FLATTEN {symbol}: initial position={initial_qty}")

            if initial_qty == 0:
                # No position — just cancel any orphan orders
                orders_cancelled = await self._cancel_all_orders(symbol)
                final_pos = await self.adapter.get_position(symbol)
                elapsed = (datetime.now(tz=timezone.utc) - started_at).total_seconds()
                logger.info(f"FLATTEN {symbol}: was already flat. Cancelled {orders_cancelled} orders.")
                return FlattenResult(
                    success=True, symbol=symbol,
                    initial_position=0, final_position=0,
                    orders_cancelled=orders_cancelled, elapsed_sec=elapsed,
                )

            # ── Step 2: Submit market close order ─────────────────────────────
            close_side = OrderSide.SELL if initial_qty > 0 else OrderSide.BUY
            close_qty = abs(initial_qty)

            close_intent = OrderIntent(
                symbol=symbol,
                side=close_side,
                quantity=close_qty,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.IOC,  # Immediate or Cancel — no orphan
                client_order_id=f"FLATTEN_{symbol}_{int(started_at.timestamp())}",
            )

            logger.info(f"FLATTEN {symbol}: submitting market close {close_side.value} {close_qty}")
            ack = await self.adapter.submit_order(close_intent)
            logger.info(f"FLATTEN {symbol}: close order submitted broker_id={ack.broker_order_id}")

            # ── Step 3: Poll until flat or timeout ────────────────────────────
            flat = await self._wait_for_flat(symbol, initial_qty)

            # ── Step 4: Cancel all remaining open orders ──────────────────────
            orders_cancelled = await self._cancel_all_orders(symbol)
            logger.info(f"FLATTEN {symbol}: cancelled {orders_cancelled} open orders")

            # ── Step 5: Final verification ────────────────────────────────────
            final_pos = await self.adapter.get_position(symbol)
            final_qty = final_pos.quantity

            # ── Step 6: Double-fill race detection ────────────────────────────
            if final_qty != 0:
                # Check if this is an accidental reversal (double-fill)
                # Reversal: we were long, close filled, then another fill came in
                # and now we are short (or vice versa)
                if (initial_qty > 0 and final_qty < 0) or (initial_qty < 0 and final_qty > 0):
                    reversal_detected = True
                    logger.critical(
                        f"🚨 FLATTEN {symbol}: DOUBLE-FILL RACE DETECTED. "
                        f"Initial={initial_qty}, Final={final_qty}. "
                        f"Attempting auto-close of reversal."
                    )
                    reversal_closed = await self._close_reversal(symbol, final_qty)
                    final_pos = await self.adapter.get_position(symbol)
                    final_qty = final_pos.quantity

            elapsed = (datetime.now(tz=timezone.utc) - started_at).total_seconds()
            success = final_qty == 0

            if success:
                logger.info(f"✅ FLATTEN {symbol}: complete in {elapsed:.1f}s")
            else:
                logger.critical(
                    f"❌ FLATTEN {symbol}: INCOMPLETE after {elapsed:.1f}s. "
                    f"Position still {final_qty}. OPERATOR INTERVENTION REQUIRED."
                )

            return FlattenResult(
                success=success,
                symbol=symbol,
                initial_position=initial_qty,
                final_position=final_qty,
                orders_cancelled=orders_cancelled,
                reversal_detected=reversal_detected,
                reversal_closed=reversal_closed,
                elapsed_sec=elapsed,
                error=None if success else f"Position {final_qty} remains after flatten",
            )

        except Exception as e:
            elapsed = (datetime.now(tz=timezone.utc) - started_at).total_seconds()
            logger.critical(f"❌ FLATTEN {symbol}: EXCEPTION after {elapsed:.1f}s: {e}")
            try:
                final_pos = await self.adapter.get_position(symbol)
                final_qty = final_pos.quantity
            except Exception:
                final_qty = -9999  # Unknown — worst case sentinel
            return FlattenResult(
                success=False,
                symbol=symbol,
                initial_position=initial_qty if 'initial_qty' in dir() else 0,
                final_position=final_qty,
                orders_cancelled=orders_cancelled,
                reversal_detected=reversal_detected,
                reversal_closed=reversal_closed,
                elapsed_sec=elapsed,
                error=str(e),
            )

    async def _wait_for_flat(self, symbol: str, initial_qty: int) -> bool:
        """Poll until position == 0 or timeout. Returns True if flat."""
        deadline = asyncio.get_event_loop().time() + self.timeout
        while asyncio.get_event_loop().time() < deadline:
            pos = await self.adapter.get_position(symbol)
            if pos.quantity == 0:
                return True
            await asyncio.sleep(self.poll_interval)
        logger.error(f"FLATTEN {symbol}: timed out after {self.timeout}s waiting for flat.")
        return False

    async def _cancel_all_orders(self, symbol: str) -> int:
        """Cancel all open orders for symbol. Returns count cancelled."""
        open_orders = await self.adapter.get_open_orders(symbol)
        cancelled = 0
        for order in open_orders:
            try:
                result = await self.adapter.cancel_order(order.broker_order_id)
                if result:
                    cancelled += 1
            except Exception as e:
                logger.error(f"FLATTEN: failed to cancel order {order.broker_order_id}: {e}")
        return cancelled

    async def _close_reversal(self, symbol: str, reversal_qty: int) -> bool:
        """
        Attempt to close an accidental reversal position.
        Returns True if successfully closed.
        """
        close_side = OrderSide.SELL if reversal_qty > 0 else OrderSide.BUY
        for attempt in range(1, MAX_REVERSAL_CLOSE_ATTEMPTS + 1):
            try:
                intent = OrderIntent(
                    symbol=symbol,
                    side=close_side,
                    quantity=abs(reversal_qty),
                    order_type=OrderType.MARKET,
                    time_in_force=TimeInForce.IOC,
                    client_order_id=f"REVERSAL_CLOSE_{symbol}_{attempt}",
                )
                await self.adapter.submit_order(intent)
                await asyncio.sleep(self.poll_interval * 2)
                pos = await self.adapter.get_position(symbol)
                if pos.quantity == 0:
                    logger.info(f"✅ Reversal closed on attempt {attempt}")
                    return True
            except Exception as e:
                logger.error(f"Reversal close attempt {attempt} failed: {e}")
        logger.critical(f"❌ REVERSAL CLOSE FAILED after {MAX_REVERSAL_CLOSE_ATTEMPTS} attempts.")
        return False

    async def flatten_all(self, symbols: List[str], reason: str = "UNSPECIFIED") -> List[FlattenResult]:
        """
        Flatten all positions across multiple symbols concurrently.
        Returns list of FlattenResult, one per symbol.
        """
        tasks = [self.flatten(symbol, reason=reason) for symbol in symbols]
        return await asyncio.gather(*tasks)
