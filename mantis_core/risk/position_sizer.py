from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PositionSize:
    quantity: float
    notional_value: float
    risk_amount: float
    risk_pct: float
    max_loss: float


class PositionSizer:
    def __init__(self, max_risk_pct: float = 0.02,
                 max_position_pct: float = 0.25,
                 min_quantity: float = 0.0001):
        if not (0.0 < max_risk_pct <= 1.0):
            raise ValueError("max_risk_pct must be in range (0.0, 1.0]")
        if not (0.0 < max_position_pct <= 1.0):
            raise ValueError("max_position_pct must be in range (0.0, 1.0]")

        self.max_risk_pct = max_risk_pct
        self.max_position_pct = max_position_pct
        self.min_quantity = min_quantity

    def size_position(self, equity: float, entry_price: float,
                      stop_loss: float, risk_pct: Optional[float] = None) -> PositionSize:
        if equity <= 0:
            raise ValueError("equity must be greater than 0")
        if entry_price <= 0:
            raise ValueError("entry_price must be greater than 0")
        if stop_loss <= 0:
            raise ValueError("stop_loss must be greater than 0")
        if stop_loss == entry_price:
            raise ValueError("stop_loss cannot equal entry_price")

        effective_risk_pct = risk_pct if risk_pct is not None else self.max_risk_pct
        effective_risk_pct = min(effective_risk_pct, self.max_risk_pct)

        risk_amount = equity * effective_risk_pct

        stop_distance = abs(entry_price - stop_loss)

        raw_quantity = risk_amount / stop_distance

        max_notional_value = equity * self.max_position_pct
        capped_notional_value = min(raw_quantity * entry_price, max_notional_value)
        capped_quantity = capped_notional_value / entry_price

        final_quantity = int(capped_quantity / self.min_quantity) * self.min_quantity

        if final_quantity < self.min_quantity:
            return PositionSize(
                quantity=0.0,
                notional_value=0.0,
                risk_amount=0.0,
                risk_pct=0.0,
                max_loss=0.0
            )

        notional_value = final_quantity * entry_price
        max_loss = final_quantity * stop_distance

        return PositionSize(
            quantity=final_quantity,
            notional_value=notional_value,
            risk_amount=risk_amount,
            risk_pct=effective_risk_pct,
            max_loss=max_loss
        )
