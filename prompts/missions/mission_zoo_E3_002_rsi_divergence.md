# MISSION: E3_002 — RSI_DIVERGENCE
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 3
GRAVEYARD_CONTEXT: E1 died from chained indexing, talib, missing .loc[]. E2.5 resurrections applied these fixes. Continue this discipline.

## BLUEPRINT
Detect RSI divergence from price. When price makes new high but RSI doesn't confirm, fade the move. Classic momentum exhaustion signal.

## PHYSICS ENGINE CONSTRAINTS (HARD)
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- No external API calls
- Output valid Python only

## DELIVERABLE
File: antigravity_harness/strategies/lab/v_zoo_e3_002/v_zoo_e3_002_rsi_divergence.py
