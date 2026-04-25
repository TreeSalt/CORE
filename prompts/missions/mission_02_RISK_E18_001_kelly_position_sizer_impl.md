# MISSION: mantis_position_sizer_kelly_impl
TYPE: IMPLEMENTATION
MISSION_ID: 02_RISK_E18_001_kelly_position_sizer_impl

## DELIVERABLE
File: mantis_core/risk/kelly_position_sizer.py

## INTERFACE CONTRACT
### Function: kelly_fraction(edge: float, variance: float, fractional: float = 0.5) -> float
### Function: position_size_from_kelly(account_value, kelly_frac, max_position_pct) -> float
### Dataclass: PositionSizeResult (frozen)
