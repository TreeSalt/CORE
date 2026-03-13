# MISSION: Strategy Interface Adapter
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_strategy_adapter
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Zoo Epoch 1 strategies implement `generate_signals(bars: pd.DataFrame) -> pd.Series`.
The backtest engine expects `Strategy.prepare_data(df, params) -> pd.DataFrame` returning
columns: entry_signal (bool), exit_signal (bool), ATR (float).

## BLUEPRINT
Create a class `ZooStrategyAdapter(Strategy)` that:
1. Wraps any Zoo strategy (passed as constructor arg)
2. Implements `prepare_data()` by calling the wrapped strategy's `generate_signals()`
3. Converts signal Series (1/-1/0) into entry_signal/exit_signal booleans
4. Computes ATR from the bars DataFrame (20-period True Range method)
5. Returns the enriched DataFrame

## DELIVERABLE
File: antigravity_harness/strategies/zoo_adapter.py

## PANDAS RULES (Epoch 1 Graveyard)
- NEVER use chained indexing. ALWAYS use .loc[]
- Use parentheses around ALL boolean comparisons
- NEVER import talib

## CONSTRAINTS
- Must work with ALL 5 Zoo E1 strategies without modification
- No hardcoded parameters
- No external API calls
- Output valid Python only
