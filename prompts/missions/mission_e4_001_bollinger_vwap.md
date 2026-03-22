# MISSION: E4_001 — Bollinger-VWAP Hybrid
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 4

## CONTEXT
E2_001 Bollinger Squeeze survived the Predatory Gate (0.9% DD, 9 trades).
E2_002 VWAP Reversion survived (0.0% DD, 4 trades).
This hybrid combines both parents: enter when Bollinger bandwidth hits
compression AND price deviates >1.5 stddev from VWAP simultaneously.
Double confirmation = higher conviction entries.

## PHYSICS ENGINE CONSTRAINTS
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- No external API calls
- Output valid Python only

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_e4_001/v_zoo_e4_001_bollinger_vwap_hybrid.py
