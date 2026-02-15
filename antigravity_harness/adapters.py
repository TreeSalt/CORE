from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from antigravity_harness.types import Money, Price, Quantity


class LiveAdapter(ABC):
    """
    Sovereign Execution Adapter.
    Interface for bridging simulation physics to live exchange protocols.
    """

    @abstractmethod
    def get_balance(self, asset: str) -> Money:
        """Retrieve actual balance from the exchange."""
        pass

    @abstractmethod
    def execute_order(
        self, symbol: str, side: str, qty: Quantity, order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        """Submit a trade to the exchange."""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Price:
        """Fetch real-time price snapshot."""
        pass


class DryRunAdapter(LiveAdapter):
    """
    Fiduciary Safety Adapter: Dry Run (Paper Trading).
    Simulates execution against local data without emitting network orders.
    """

    def __init__(self, initial_balances: Optional[Dict[str, float]] = None):
        self._balances = initial_balances or {"USD": 100000.0}
        self._order_log: List[Dict[str, Any]] = []

    def get_balance(self, asset: str) -> Money:
        return Money(self._balances.get(asset, 0.0))

    def execute_order(
        self, symbol: str, side: str, qty: Quantity, order_type: str = "MARKET"
    ) -> Dict[str, Any]:
        # Simulating execution latency and success
        result = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "status": "FILLED",
            "message": "DryRun: Order simulating bit-perfect execution.",
        }
        self._order_log.append(result)
        return result

    def get_ticker(self, symbol: str) -> Price:
        # In multi-phase logic, this would pull from the latest Gurgler price.
        return Price(0.0)
