# MISSION: E3_004 — OVERNIGHT_RANGE_TRAP
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 3
GRAVEYARD_CONTEXT: E1 died from chained indexing, talib, missing .loc[]. E2.5 resurrections applied these fixes. Continue this discipline.

## BLUEPRINT
Detect when the opening 15min price is within the overnight high-low range. If range is tight (<0.5%), bet on breakout in the direction of the first 15min close.

## PHYSICS ENGINE CONSTRAINTS (HARD)
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- No external API calls
- Output valid Python only

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_e3_004/v_zoo_e3_004_overnight_range_trap.py
