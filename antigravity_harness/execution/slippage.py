"""
antigravity_harness/execution/slippage.py
=========================================
Mandatory friction models for TRADER_OPS.
"""
from decimal import Decimal

from antigravity_harness.execution.adapter_base import OrderSide


class PhysicsViolationError(Exception):
    """Raised when an order violates asset class physics."""
    pass

def apply_mes_friction(base_price: float, side: OrderSide, quantity: int) -> tuple[Decimal, float]:
    """
    Applies mandatory MES friction:
    - Min 1 tick slippage (0.25)
    - $0.35 commission per side per contract
    """
    tick_size = 0.25
    commission_per_contract = 0.85
    
    slippage = tick_size
    fill_price = base_price + slippage if side == OrderSide.BUY else base_price - slippage
        
    total_commission = commission_per_contract * quantity
    return Decimal(str(round(fill_price, 4))), float(total_commission)
