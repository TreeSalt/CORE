# MISSION: Implement Zoo Variant ZOO_E2_004 — VOLUME_CLIMAX_FADE
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E2_004
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 2
GRAVEYARD_CONTEXT: E1 lessons — no chained indexing, no talib, parentheses on booleans.

## CONTEXT
Fade extreme volume spikes. When volume exceeds 3x 20-bar average AND price makes new high, SHORT the exhaustion.

## PHYSICS ENGINE CONSTRAINTS (HARD)
- allow_fractional_shares=False (MES)
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- Inherit from: antigravity_harness.strategies.base.Strategy
- Implement: prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame
- Return df must contain: entry_signal (bool), exit_signal (bool), ATR (float)

## PANDAS RULES
- ALWAYS use .loc[] — NEVER chained indexing
- NEVER import talib
- Parentheses around ALL boolean: (a > b) & (c < d)

## DELIVERABLE
File: antigravity_harness/strategies/lab/v_zoo_zoo_e2_004/v_zoo_zoo_e2_004.py

## CONSTRAINTS
- No hardcoded parameters — derive dynamically
- No external API calls, no overnight positions
- Output valid Python only
