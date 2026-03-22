# MISSION: E3_003 — MARKET_PROFILE_VALUE
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 3
GRAVEYARD_CONTEXT: E1 died from chained indexing, talib, missing .loc[]. E2.5 resurrections applied these fixes. Continue this discipline.

## BLUEPRINT
Identify the Point of Control (highest volume price) from the prior session. Trade mean reversion toward POC when price deviates >1 ATR.

## PHYSICS ENGINE CONSTRAINTS (HARD)
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- No external API calls
- Output valid Python only

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_e3_003/v_zoo_e3_003_market_profile_value.py
