# antigravity_harness/compliance.py
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List


class GovernanceViolationError(Exception):
    """Raised when a quarantined strategy violates tier governance."""
    pass


@dataclass
class OrderIntent:
    symbol: str
    side: str
    qty: Decimal
    price: Decimal
    type: str


class ComplianceOfficer:
    def __init__(self):
        self.logger = logging.getLogger("FIDUCIARY_COMPLIANCE")
        self.open_orders: List[OrderIntent] = []

    def vet_intent(
        self, intent: OrderIntent, current_mid_price: float, portfolio_state: Any = None
    ) -> tuple[bool, str]:
        # 1. WASH TRADE GUARD
        for open_order in self.open_orders:
            if (
                open_order.symbol == intent.symbol
                and open_order.side != intent.side
                and self._is_crossing(intent, open_order)
            ):
                msg = "🚨 [CRIME] WASH TRADE BLOCKED."
                self.logger.critical(msg)
                return False, msg

        # 2. FAT FINGER GUARD
        if intent.type == "LIMIT":
            deviation = abs(float(intent.price) - current_mid_price) / current_mid_price
            if deviation > 0.05:  # noqa: PLR2004
                msg = f"🚨 [RISK] FAT FINGER BLOCKED. Deviation: {deviation * 100:.2f}%"
                self.logger.critical(msg)
                return False, msg

        return True, "APPROVED"

    def _is_crossing(self, new_order: OrderIntent, open_order: OrderIntent) -> bool:
        if new_order.side == "BUY":
            return new_order.price >= open_order.price
        else:
            return new_order.price <= open_order.price
