# MISSION: Implement Zoo Variant ZOO_E2_003 — TRIPLE_EMA_CASCADE
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E2_003
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 2
GRAVEYARD_CONTEXT: E1 lessons — no chained indexing, no talib, parentheses on booleans.

## CONTEXT
Three EMA cascade (8/21/55). Enter only when all three aligned AND price pulls back to 21 EMA.

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
File: mantis_core/strategies/lab/v_zoo_zoo_e2_003/v_zoo_zoo_e2_003.py

## CONSTRAINTS
- No hardcoded parameters — derive dynamically
- No external API calls, no overnight positions
- Output valid Python only
