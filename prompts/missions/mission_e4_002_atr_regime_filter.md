# MISSION: E4_002 — ATR Regime Filter
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 4

## CONTEXT
The Predatory Gate kills strategies that trade during high-volatility regimes.
This strategy is PURELY DEFENSIVE: it computes a regime score from ATR expansion
rate, and only allows other strategies to trade when the regime is favorable.
It acts as a portfolio-level filter, not a standalone signal generator.

Returns entry_signal=False always. Returns exit_signal=True when regime is dangerous.
Strategies downstream check this filter before entering positions.

## PHYSICS ENGINE CONSTRAINTS
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- No external API calls
- Output valid Python only

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_e4_002/v_zoo_e4_002_atr_regime_filter.py
