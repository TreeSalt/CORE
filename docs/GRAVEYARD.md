# STRATEGY ZOO — GRAVEYARD
## Anti-Pattern Memory Ledger
**Status:** INITIALIZED
**Version:** v9.9.12
**Ratified:** 2026-03-10 — Alec W. Sanchez, Sovereign

**Purpose:** Immutable record of failed strategy topologies and their cause of death.
Fed to the 32B Heavy Lifter as negative context during Alpha Synthesis.
The Graveyard is as valuable as the Champion Registry.

**Format:** Each entry records strategy ID, core logic summary, failure mode,
market condition at time of death, and lessons extracted.

**Append-only:** No entry may be deleted or modified. Ever.

---

## Entry Schema
Each entry must contain:
- **Strategy ID** — unique identifier
- **Generation / Epoch** — which Zoo epoch produced this strategy
- **Core Logic Summary** — entry/exit topology, timeframe, parameters
- **Cause of Death** — which gate it failed, what threshold it breached
- **Market Condition at Death** — regime, volatility state, macro context
- **Lesson Extracted** — what NOT to generate in the next epoch

---

## Entries

*(No entries yet — Zoo not yet operational. First entries will be written
automatically by the epoch culling process when Generation 1 Zoo completes.)*

## ANTI-PATTERN: websocket.SSLOpt.CERT_NONE
- **First seen:** v4.7.54 (Founding Incident)
- **Re-emerged:** v9.9.25 — 7b sprinter, WebSocketHandler
- **Correct form:** `ssl.CERT_NONE` from stdlib `ssl` module
- **websocket-client** has no `SSLOpt` attribute — always use stdlib ssl
- **Detection:** pytest AttributeError, caught by Gate 3 LOGIC
- **Resolution:** factory self-corrected via benchmark feedback loop


## Predatory Gate — 2026-03-13
- **E1_001**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E1_001_VOLATILITY_GATEKEEPER**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E1_002_MEAN_REVERSION_SNIPER**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E1_003_REGIME_CHAMELEON**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E1_004_OPENING_RANGE_BREAKOUT**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E1_005_MOMENTUM_DECAY_HARVESTER**: Load failed: cannot import name 'BaseStrategy' from 'mantis_core.strategies.base' (/home/asanchez/TRADER_OPS/v9e_stage/mantis_core/strategies/base.py)
- **E2_003**: Predatory Gate: 99.90% DD
- **E2_004**: Load failed: name 'mantis_core' is not defined
- **unknown**: Load failed: No strategy class found


## Predatory Gate v2 — 2026-03-13
- **E1_001_VOLATILITY_GATEKEEPER**: Predatory Gate v2: 99.90% DD
- **E1_002_MEAN_REVERSION_SNIPER**: Predatory Gate v2: 99.90% DD
- **E1_003_REGIME_CHAMELEON**: Load failed: No module named 'talib'
- **E1_004_OPENING_RANGE_BREAKOUT**: Predatory Gate v2: 99.90% DD
- **E1_005_MOMENTUM_DECAY_HARVESTER**: Predatory Gate v2: 99.90% DD


## Predatory Gate v2 — 2026-03-15
- **E1_001_VOLATILITY_GATEKEEPER**: Predatory Gate v2: 99.90% DD
- **E1_002_MEAN_REVERSION_SNIPER**: Predatory Gate v2: 99.90% DD
- **E1_003_REGIME_CHAMELEON**: Load failed: No module named 'talib'
- **E1_004_OPENING_RANGE_BREAKOUT**: Predatory Gate v2: 99.90% DD
- **E1_005_MOMENTUM_DECAY_HARVESTER**: Predatory Gate v2: 99.90% DD
- **E2_001_BOLLINGER_SQUEEZE**: Predatory Gate v2: 99.90% DD
- **E2_002_VWAP_REVERSION**: Load failed: No strategy class found
- **unknown**: Predatory Gate v2: 99.90% DD
