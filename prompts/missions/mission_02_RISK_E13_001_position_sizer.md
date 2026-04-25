# MISSION: Risk-Based Position Sizer
DOMAIN: 02_RISK_MANAGEMENT
TASK: 02_RISK_E13_001_position_sizer
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Position sizing determines how much capital to deploy on each trade based
on account equity, risk tolerance, and stop distance. This is the only
module standing between MANTIS and ruin — it must enforce hard caps and
fail loud on invalid inputs.

The previous E11 attempt produced unusable stream-of-consciousness code
with two duplicate class definitions. This mission builds the proper version.

## EXACT IMPORTS:
```python
from dataclasses import dataclass
from typing import Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/risk/position_sizer.py` containing:

### Dataclass: PositionSize
Frozen dataclass with these exact fields:
```
quantity: float                  # number of units to trade
notional_value: float            # quantity * entry_price
risk_amount: float               # absolute dollar risk
risk_pct: float                  # risk as fraction of equity
max_loss: float                  # quantity * |entry - stop|
```

### Class: PositionSizer
Constructor accepts these parameters with defaults:
- max_risk_pct: float = 0.02         (2% maximum risk per trade)
- max_position_pct: float = 0.25     (25% maximum position size of equity)
- min_quantity: float = 0.0001       (minimum tradeable unit)

The constructor must raise ValueError if max_risk_pct or max_position_pct
are not in (0.0, 1.0].

Method: `size_position(self, equity: float, entry_price: float, stop_loss: float, risk_pct: Optional[float] = None) -> PositionSize`

The method must:
1. Validate equity > 0, raise ValueError otherwise
2. Validate entry_price > 0, raise ValueError otherwise
3. Validate stop_loss > 0, raise ValueError otherwise
4. Validate stop_loss != entry_price, raise ValueError otherwise
5. Use risk_pct parameter if provided, otherwise use self.max_risk_pct
6. Cap effective risk_pct at self.max_risk_pct (never exceed configured max)
7. Compute risk_amount = equity * effective_risk_pct
8. Compute stop_distance = abs(entry_price - stop_loss)
9. Compute raw quantity = risk_amount / stop_distance
10. Cap raw quantity such that quantity * entry_price <= equity * max_position_pct
11. Round down to nearest min_quantity increment
12. If final quantity < min_quantity, return PositionSize with all zeros
13. Return populated PositionSize dataclass

## DELIVERABLE
File: mantis_core/risk/position_sizer.py

## BEHAVIORAL REQUIREMENTS
- Deterministic: same input always produces same output
- Pure Python: no numpy, no pandas, no external libraries
- No file I/O, no network calls, no global state
- Fail loud on invalid input (raise ValueError, never return garbage)
- Never exceed max_risk_pct or max_position_pct caps
- Quantity must always be a multiple of min_quantity

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. Constructor raises ValueError for risk_pct outside (0, 1]
2. size_position raises ValueError for non-positive equity
3. size_position raises ValueError for non-positive prices
4. size_position raises ValueError when stop_loss == entry_price
5. risk_amount never exceeds equity * max_risk_pct
6. notional_value never exceeds equity * max_position_pct
7. quantity is always a multiple of min_quantity
8. Returns zero PositionSize when quantity would be below min_quantity
9. Same input produces same output (deterministic)

## CONSTRAINTS
- Pure stdlib (dataclasses + typing only)
- No external dependencies
- Output valid Python only
