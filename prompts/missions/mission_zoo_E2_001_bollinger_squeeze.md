# MISSION: Implement Zoo Variant ZOO_E2_001 — BOLLINGER_SQUEEZE
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E2_001
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 2
GRAVEYARD_CONTEXT: E1 lessons — no chained indexing, no talib, parentheses on booleans.

## CONTEXT
Bollinger Band width contraction detector. Enter when bandwidth hits 6-month low, exit when bands expand 2x.

## PHYSICS ENGINE CONSTRAINTS (HARD)
- allow_fractional_shares=False (MES)
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- Inherit from: mantis_core.strategies.base.Strategy
- Implement: prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame
- Return df must contain: entry_signal (bool), exit_signal (bool), ATR (float)

## PANDAS RULES
- ALWAYS use .loc[] — NEVER chained indexing
- NEVER import talib
- Parentheses around ALL boolean: (a > b) & (c < d)

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_zoo_e2_001/v_zoo_zoo_e2_001.py

## CONSTRAINTS
- No hardcoded parameters — derive dynamically
- No external API calls, no overnight positions
- Output valid Python only
