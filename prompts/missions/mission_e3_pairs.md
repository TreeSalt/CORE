# MISSION: Epoch 3 — Correlation/Pairs Strategy
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_correlation_strategy
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 3

## CONTEXT
All existing Zoo strategies are single-instrument (MES only). A new topology:
correlation-based strategies that detect when MES deviates from a synthetic
moving benchmark and trades the reversion.

## BLUEPRINT
Create a SyntheticPairsStrategy that:
1. Computes a rolling correlation between MES close and its own 50-bar SMA
2. When correlation breaks below -0.5 (price diverges from trend), enter long
3. When correlation returns above 0.0 (convergence), exit
4. ATR-based position sizing (1 contract max)
5. No overnight, max 3 trades/day

This is a SELF-REFERENTIAL pairs trade: the "pair" is price vs its own trend.
No external data required.

## DELIVERABLE
File: antigravity_harness/strategies/lab/v_zoo_E3_001/v_zoo_E3_001_synthetic_pairs.py

## PHYSICS ENGINE CONSTRAINTS
- Inherit from Strategy, implement prepare_data()
- Return entry_signal, exit_signal, ATR
- .loc[] only, no talib, parentheses on booleans
- No external API calls
- Output valid Python only
