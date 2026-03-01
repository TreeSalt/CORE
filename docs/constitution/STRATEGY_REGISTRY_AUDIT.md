# Strategy Registry Audit (v4.6.1)

This document provides a formal audit of the TRADER_OPS strategy landscape as of February 2026. It categorizes existing strategies by their physical generation and documents the migration requirements for the **IntentSpec** (v050+) standard.

## Registry Snapshot

| Strategy ID | Tier | Generation | Status |
| :--- | :--- | :--- | :--- |
| `v040_alpha_prime` | Certified | v040 | **Active Smoke Anchor**. Requires v050 wrapper. |
| `v080_volatility_guard`| Certified | v080 | Certified for Paper. High-fidelity risk controls. |
| `v060_bit_uni_core`| Lab | v060 | In-situ testing for high-regime volatility. |
| `v050_trend_momentum` | Quarantine | v050 | **Intent-Native**. Blueprint for future strategies. |
| `EQ_SENTIMENT_v1` | Quarantine | v050-Alt | Alt-data dependency detected. Policy required. |

## Generation Roadmap

### Generation v040: Data-Driven Signals
Strategies in this generation output raw boolean signals (`entry_signal`, `exit_signal`). 
- **Audit Finding**: Directly coupled to the backtest engine. 
- **Migration**: Requires `V050_Intent_Wrapper` to propose `OrderIntent` objects.

### Generation v050: Intent-Driven (IntentSpec)
Strategies in this generation implement the `IntentStrategy` interface.
- **Audit Finding**: Properly decoupled from execution. Proposes `StrategySignal`.
- **Compliance**: Aligns with the Phase 2 **Action Authorization Engine**.

### Generation v060+: Higher-Regime Physics
Emerging strategies focusing on vectorized scaling and hypercube lookups.
- **Audit Finding**: Currently in Lab tier. Requires Sovereign Audit before Promotion.

## Compliance Requirements

To achieve **Fiduciary Graduation** in Phase 2, all `Certified` strategies must:
1. Satisfy the `INTENT_SPEC.schema.json`.
2. Be verifiable via the `Action Authorization Engine`.
3. Emit structured `StrategySignal` metadata for the forensic `fill_tape.csv`.
