
---
## AMENDMENT: 2026-03-09 — Intelligence Roster Correction (replaces AOS-001 model list)

### THREE-TIER INTELLIGENCE STACK — CANONICAL

**TIER 1 — AGENTIC EXECUTORS (Sprinters)**
- qwen2.5:7b           — Local Vanilla Sprinter
- qwen2.5-coder:7b     — Local Coder Sprinter
- Claude Code          — Cloud Coder Sprinter

**TIER 2 — AGENTIC ORCHESTRATORS (Heavy Lifters)**
- qwen2.5:32b          — Local Vanilla Heavy Lifter / Local Orchestrator
- qwen2.5-coder:32b    — Local Coder Heavy Lifter / Local Orchestrator
- Claude Code          — Cloud Heavy Lifter / Cloud Orchestrator (dual role)

**TIER 3 — AGENTIC ARCHITECTS (Supreme Council)**
- qwen2.5:72b          — ASPIRING Local Vanilla Supreme
- qwen2.5-coder:72b    — ASPIRING Local Coder Supreme
- Claude.ai            — Cloud Chief Strategist & Developer
- gemini.google.com    — Cloud Chief Visionary & Researcher

**THE HUMAN IN THE LOOP**
- Alec W. Sanchez      — Sovereign. Origin of the idea. Final authority on all things.

Ratified by: Alec W. Sanchez
Date: 2026-03-09

---

## [DECISION-THRESHOLD-001] 2026-03-10 — CP1→CP2 Advancement Gate: Phase 3 Profitability Threshold

**Author:** Alec W. Sanchez (Sovereign)
**Ratified by:** Supreme Council
**Status:** SEALED

### DECISION

The following thresholds are now constitutional requirements for CP1→CP2 advancement.
No agent may propose, and no human may authorize, advancement to CP2_MICRO_CAPITAL
without ALL THREE gates passing simultaneously. These numbers are non-negotiable and
may only be amended by a human-authored DECISION_LOG entry with stated justification.

### GATE 1 — MINIMUM RUN DURATION
- **Requirement:** 90–120 trading days (calendar) OR 250–300 independent closed trades,
  whichever comes LATER. Both conditions must be satisfied.
- **Rationale:** Statistical significance. A Sharpe ratio computed on fewer than 250
  independent trades is noise, not signal. 90 days minimum ensures the system has
  been exposed to at least one full macro regime cycle.
- **Enforcement:** `make quickgate` must verify trade count from the immutable trade
  ledger and session start timestamp before surfacing CP2 eligibility.

### GATE 2 — MINIMUM PAPER SHARPE RATIO
- **Requirement:** Rolling 90-day paper Sharpe Ratio ≥ 2.5 (target: 3.0)
- **Rationale:** The institutional live trading floor is Sharpe ≥ 1.0. To absorb
  real-world execution costs (slippage, spread, latency, partial fills, broker fees),
  the paper system must carry a 2.5x–3.0x buffer. A paper Sharpe of 2.5 that degrades
  50% under live conditions still clears the institutional floor at 1.25. This is the
  shock absorber. Anything below 2.5 in paper has no margin of safety in production.
- **Enforcement:** Computed on annualized basis using daily P&L from the paper ledger.
  Sharpe = (Mean Daily Return / StdDev Daily Return) × √252

### GATE 3 — MAXIMUM DRAWDOWN
- **Requirement:** Maximum drawdown in paper must never exceed 15% of simulated capital
  at any point during the qualifying run.
- **Rationale:** 15% is the strict maximum. A system that draws down 15% in frictionless
  paper will draw down further under live conditions. Any breach of 15% in paper
  disqualifies the current run entirely — the clock resets to zero, a new qualifying
  run must begin, and the breach must be logged in the ERROR_LEDGER with root cause.
- **Enforcement:** Dead Man's Switch monitors real-time drawdown. A paper drawdown
  breach triggers the same FAIL-CLOSED response as a live capital breach.

### SUMMARY TABLE

| Gate | Metric | Threshold | Breach Action |
|------|--------|-----------|---------------|
| G1 | Run duration | ≥ 90 trading days AND ≥ 250 trades | Clock resets |
| G2 | Rolling 90d Sharpe | ≥ 2.5 (target 3.0) | Ineligible until sustained |
| G3 | Max drawdown | ≤ 15% of simulated capital | Run disqualified, clock resets |

### WHAT THIS MEANS

The system cannot rush to live capital. If it takes 6 months in paper to produce
a qualifying run, that is the correct answer. Speed is not the objective. A
single catastrophic live loss from premature advancement would set the project back
further than 6 months of patient paper trading ever could.

**Ratified by:** Alec W. Sanchez
**Date:** 2026-03-10
