"""
adapter_base.py — Execution Adapter Contract
=============================================
Abstract base class defining the sovereign execution interface.
All adapters (sim, live, paper) must implement this contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderSide(Enum):
    """Trade direction."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order execution type."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(Enum):
    """Lifecycle status of an order."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Order:
    """Immutable order record."""
    order_id: str
    symbol: str
    side: OrderSide
    qty: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Fill:
    """Immutable fill record — proof of execution."""
    order_id: str
    symbol: str
    side: OrderSide
    qty: float
    fill_price: float
    expected_price: float
    slippage: float
    commission: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def slippage_bps(self) -> float:
        """Slippage in basis points relative to expected price."""
        if self.expected_price <= 0:
            return 0.0
        return ((self.fill_price - self.expected_price) / self.expected_price) * 10000.0


class ExecutionAdapter(ABC):
    """
    Sovereign Execution Adapter — Abstract Base.

    Defines the contract for all execution backends.
    Implementations must be:
      - Deterministic in sim mode
      - Auditable (every order/fill logged)
      - Fail-closed (reject on uncertainty)
    """

    @abstractmethod
    def submit_order(self, order: Order) -> Fill:
        """
        Submit an order and return the resulting fill.

        Raises:
            ExecutionError: If the order cannot be executed.
        """

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Attempt to cancel a pending order.

        Returns True if cancellation was successful, False if already filled.
        """

    @abstractmethod
    def get_fills(self, symbol: Optional[str] = None) -> List[Fill]:
        """
        Retrieve fill history, optionally filtered by symbol.
        """

    @abstractmethod
    def get_position(self, symbol: str) -> float:
        """
        Get current net position for a symbol.
        Returns signed quantity (positive = long, negative = short, 0 = flat).
        """

    @abstractmethod
    def get_cash(self) -> float:
        """Get current available cash balance."""


class ExecutionError(Exception):
    """Raised when an order cannot be executed."""

    def __init__(self, message: str, order: Optional[Order] = None,
                 reason: str = "UNKNOWN"):
        super().__init__(message)
        self.order = order
        self.reason = reason
