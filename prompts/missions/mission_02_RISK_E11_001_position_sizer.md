# MISSION: MANTIS Position Sizer — ATR-Based Risk Manager
DOMAIN: 02_RISK_MANAGEMENT
TASK: 02_RISK_E11_001_position_sizer
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
No trade without a position size. The position sizer determines capital allocation
based on volatility, equity, and fixed risk-per-trade. This is MANTIS's fiduciary layer.

## BLUEPRINT
1. risk_amount = equity * risk_per_trade (default 1%)
2. raw_qty = risk_amount / abs(entry - stop_loss)
3. max_qty = (equity * max_position_pct) / entry_price (default 5%)
4. final_qty = min(raw_qty, max_qty), rounded to 8 decimals

Safety: ValueError on zero equity or zero stop distance. Never negative qty.
Clamp if position value exceeds equity.

Output PositionSize dataclass: qty, risk_amount, position_value, position_pct,
risk_reward_ratio, clamped bool.

## DELIVERABLE
File: mantis_core/risk/position_sizer.py

## CONSTRAINTS
- Pure Python standard library (math, dataclasses)
- Handle all edge cases
- Output valid Python only
