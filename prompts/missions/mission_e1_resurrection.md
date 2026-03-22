# MISSION: E2.5 — Resurrect E1 Strategies With Graveyard Lessons
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_e1_resurrection
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
All 5 Epoch 1 strategies were killed in the Predatory Gate due to execution bugs:
- Chained indexing (bars['col'][cond] = val)
- Missing .loc[] usage
- Column name errors ('time' vs index)
- BaseStrategy vs Strategy import

Meanwhile, all Epoch 2 strategies that received Graveyard anti-pattern guidance survived.

## BLUEPRINT
For EACH of the 5 E1 strategy concepts, create a new FIXED implementation:
1. E2.5_001: Volatility Gatekeeper REBORN — ATR gate + EMA crossover
2. E2.5_002: Mean Reversion Sniper REBORN — VWAP + deviation entry
3. E2.5_003: Regime Chameleon REBORN — ADX regime switching (NO talib)
4. E2.5_004: Opening Range Breakout REBORN — first 30min range
5. E2.5_005: Momentum Decay Harvester REBORN — pullback after spike

Each reimplementation MUST:
- Inherit from Strategy (not BaseStrategy)
- Implement prepare_data(self, df, params, intelligence=None, vector_cache=None)
- Return DataFrame with entry_signal (bool), exit_signal (bool), ATR (float)
- Use .loc[] exclusively — NEVER chained indexing
- NEVER import talib
- Use parentheses around ALL boolean operations

Generate all 5 as a single proposal with clear class separation.

## DELIVERABLE
File: mantis_core/strategies/lab/epoch_2_5_resurrections.py

## CONSTRAINTS
- One file, 5 classes
- Each class must be independently testable
- No hardcoded parameters
- No external API calls
- Output valid Python only
