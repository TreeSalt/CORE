MISSION: Initialize Strategy Zoo Graveyard ledger
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION
VERSION: 1.0

Create the file docs/GRAVEYARD.md — the immutable anti-pattern memory ledger
for the Strategy Zoo. This file records every failed trading strategy with its
failure topology and the market condition that killed it.

REQUIREMENTS:
Write docs/GRAVEYARD.md with the following structure:

# STRATEGY ZOO — GRAVEYARD
## Anti-Pattern Memory Ledger
**Status:** INITIALIZED
**Purpose:** Immutable record of failed strategy topologies and their cause of death.
  Fed to the 32B Heavy Lifter as negative context during Alpha Synthesis.
  The Graveyard is as valuable as the Champion Registry.
**Format:** Each entry records strategy ID, core logic summary, failure mode,
  market condition at time of death, and lessons extracted.
**Append-only:** No entry may be deleted or modified.

---

## Entry Schema
Each failed strategy entry must contain:
- Strategy ID
- Generation / Epoch
- Core Logic Summary (entry/exit topology, timeframe, parameters)
- Cause of Death (which gate it failed, what threshold it breached)
- Market Condition at Death (regime, volatility state, macro context)
- Lesson Extracted (what NOT to do in the next generation)

---

## Entries
*(No entries yet — Zoo not yet operational. First entries will be written
automatically by the epoch culling process when Generation 1 completes.)*

CONSTRAINTS:
- Write to docs/ only
- No writes to 04_GOVERNANCE/
- No hardcoded credentials
- Output must be valid Markdown
