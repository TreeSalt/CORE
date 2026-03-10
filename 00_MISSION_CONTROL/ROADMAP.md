# TRADER_OPS — Strategic Roadmap
**Version:** 2.0
**Authors:** Alec W. Sanchez (Sovereign), Claude (Hostile Auditor), Gemini (Chief Visionary)
**Ratified:** 2026-03-10
**Status:** SEALED — Supreme Council Ratified

> *Quantitative thresholds, drawdown floors, and advancement gates are NOT duplicated here.*
> *This document defines strategy and architecture. All enforceable numbers live in*
> *`CHECKPOINTS.yaml` and `04_GOVERNANCE/DECISION_LOG.md` — the Single Source of Truth.*
> *If this document and those files ever conflict, those files win.*

---

## Preamble: What This Is Building

TRADER_OPS is not a trading bot. It is an **Adversarial Governance Framework** that
happens to trade. Every architectural decision exists to answer one question: *how do
you build a system that manages capital on behalf of humans without destroying them?*

The answer is not better algorithms. The answer is a system that cannot advance faster
than its own evidence of fitness — where the clock ticks in real time, where failure
leaves an immutable forensic trail, and where no agent can forge the proof of its own
competence.

This Roadmap is the strategic contract between the system and the people who built it.

---

## Phase 1 — The Monorepo & The Strategy Zoo
**Status: CURRENT**
**Checkpoint: CP1_PAPER_SANDBOX**

### Mission
Build the factory that builds the trading models. Before a single dollar of real capital
is touched, the orchestration infrastructure, sensor layer, and validation pipeline must
be proven in paper. The goal of Phase 1 is not profit — it is **proof of process**.

### Core Build Targets
- **DATA_MULTIPLEXER** — Asynchronous multi-feed ingestion with Fiduciary Air Gap.
  Normalizes raw market data into a clean, authenticated stream before any strategy
  layer ever sees it.
- **OPSEC_RAG_SCOUT** — Retrieval-augmented intelligence layer. Feeds relevant market
  context to the orchestration agents without exposing raw external data to the
  execution layer.
- **AOS Factory Domains 00–08** — All eight domains sealed at Generation 1 (complete).
  Proposal typing (ARCHITECTURE / IMPLEMENTATION) active. Benchmark Runner v1.0.0
  operational.

### The Strategy Zoo — Concurrent Generational Validation

Because the CP1 advancement gate requires a minimum forward-test window (see
`CHECKPOINTS.yaml → CP1_PAPER_SANDBOX → advancement_gates`), and because that clock
**cannot be compressed** (forward time is the fiduciary air gap between backtested
theory and unknown future regimes), TRADER_OPS runs **multiple concurrent CP1
instances in parallel**.

This is the Strategy Zoo. It operates in generational epochs.

#### Hardware Model
- **The Factory** (VRAM-bound): GTX 1070 8GB drives the LLM agents. One model at a
  time. This is the constraint on *creation speed*, not on *execution capacity*.
- **The Zoo** (RAM-bound): Each live paper-trading script consumes ~30–50MB of system
  RAM. 32GB DDR4 supports **hundreds of concurrent paper threads** across CPU cores.
  The hardware limits how fast we write bots, not how many we can run simultaneously.

#### Epoch Structure
1. **Generation Spawn** — The Factory (via orchestration router) generates a cohort of
   strategy variants. Variants differ in parameters, timeframes, entry logic, and
   position sizing. Each receives a unique ID and is registered in
   `state/champion_registry.json`.

2. **The Predatory Gate** — Before any bot enters the live paper queue, it must survive
   a synthetic Black Swan stress test: a curated dataset of the highest-volatility,
   most illiquid historical sessions on record (e.g., COVID crash March 2020, 2010
   Flash Crash, 2022 Fed pivot sessions). Any bot that breaches the drawdown threshold
   defined in `CHECKPOINTS.yaml` against this historical gauntlet is **slaughtered
   before it touches live data**. This preserves system RAM and protects data bandwidth.

3. **Concurrent CP1 Run** — Survivors enter the live paper queue simultaneously. All
   threads experience the identical real-time market regime — the same FOMC meetings,
   the same liquidity events, the same macro shocks. This produces a standardized,
   90-day comparative fitness matrix.

4. **Culling & The Graveyard** — At epoch close, underperformers are terminated. Their
   core logic (parameters, entry/exit topology, timeframe) is extracted and appended to
   `docs/GRAVEYARD.md` — an immutable anti-pattern ledger. The Graveyard records not
   just *what* failed but *what market condition* killed it.

5. **Alpha Synthesis — LLM Gene Splicing** — The 32B Heavy Lifter is fed the top
   survivors alongside the full Graveyard as negative context. It performs semantic
   analysis of the winning Abstract Syntax Trees, extracts the dominant traits from
   each, and synthesizes a new generation of hybrid strategies. This is not random
   parameter mutation — it is **intelligent architectural fusion** guided by a model
   that has read both the winners and the autopsy reports of the dead.

#### The Symbiotic Multi-Timeframe Ensemble

The most advanced construct in the Zoo. Short-timeframe micro-models (scalpers,
1-minute regime detectors) act as **forward scouts** for long-timeframe macro-models
(trend followers, daily-bar position traders).

**The key architectural principle:** The macro-model's Python source code is
**immutable** during its 90-day CP1 run. Hot-swapping source code mid-run would
dump state, break position tracking, and reset the advancement clock — a Fiduciary
HARD_FAIL. Instead, the macro-model reads its hyper-parameters on every tick from a
live `MACRO_DNA.json` file.

The signal bus works as follows:
- Micro-models complete accelerated epochs and pass the Predatory Gate
- Their winning parameters (volatility thresholds, position sizing weights,
  regime classification signals) are extracted by the 32B Orchestrator
- The Orchestrator writes a validated update to `MACRO_DNA.json`
- The macro-model's immutable core logic reads the new DNA on the next tick and
  adapts its behavior — position sizing, stop placement, exposure limits — without
  any code restart or state loss

The racehorse teaches the workhorse how to survive a drought. In real time. Without
either of them stopping.

### Phase 1 Exit Criteria
All exit criteria are defined quantitatively in `CHECKPOINTS.yaml → CP1_PAPER_SANDBOX
→ advancement_gates` and ratified in `DECISION_LOG → DECISION-THRESHOLD-001`.
This Roadmap will not duplicate those numbers. They have one home.

---

## Phase 2 — The Auto-Delegator
**Status: PENDING**
**Checkpoint: CP2_MICRO_CAPITAL**

### Mission
Replace manual routing with automated orchestration. The Human Sovereign moves from
**operator** to **auditor**. The system dispatches tasks, monitors fitness, and spawns
new Zoo epochs without requiring manual invocation — but every capital decision still
requires human-authored authorization at the sovereign gate.

### Core Build Targets
- **Automated Semantic Router** — `orchestration/semantic_router.py` evolves from
  CLI-invoked tool to daemon. Monitors mission queue, dispatches autonomously, writes
  proposals, routes to benchmark runner without human initiation.
- **Epoch Scheduler** — Automated cohort generation at configurable intervals. Manages
  Zoo population size against RAM budget. Auto-culls at epoch boundaries.
- **Live Capital Integration** — CP2 capital limit ($100 hard ceiling enforced by
  `FiduciaryBridge` + Dead Man's Switch). First real money. First real stakes.
- **Immutable Trade Ledger** — Every executed order, fill, and P&L event written to
  an append-only ledger. No delete. No edit. Forensic completeness.

### Phase 2 Exit Criteria
Defined in `CHECKPOINTS.yaml → CP2_MICRO_CAPITAL`. Human approval required.
The Dead Man's Switch (`scripts/dead_mans_switch.py`) is the mechanical enforcement
layer. It cannot be bypassed.

---

## Phase 3 — The Branch
**Status: FUTURE**
**Checkpoints: CP3_AUDIT_LEDGER**

### Mission
TRADER_OPS bifurcates. The Agentic Orchestration System (AOS) — the factory, the
governance framework, the constitutional layer — is open-sourced as a standalone
project. TRADER_OPS becomes the first commercial payload built on top of it.

Simultaneously, TRADER_OPS launches as an individual Fiduciary SaaS product: a
single-user, autonomous trading co-pilot for sophisticated retail traders who want
institutional-grade risk management without institutional-grade overhead.

### Core Build Targets
- **AOS Open-Source Fork** — Clean separation of universal engine from proprietary
  trading logic (as required by Article VII of the Constitution). The AOS contains
  no alpha. TRADER_OPS contains no governance engine. They are two separate
  repositories from this point forward.
- **Web Dashboard API** — Human-readable interface for portfolio state, epoch status,
  Zoo fitness metrics, and trade ledger. Read-only for subscribers. Write-access for
  Sovereign only.
- **Automated Tax-Loss Harvesting** — Fiduciary-compliant P&L optimization layer.
  Flags [LEGAL_REVIEW_REQUIRED] per Article III.3 before deployment.
- **Agentic Accounting & Ledger Reconciliation** — Autonomous reconciliation of
  internal trade ledger against broker statements. Discrepancy detection triggers
  FAIL-CLOSED and human review.

### Legal Gate
Texas securities attorney review is **mandatory** before any feature that touches
third-party capital, third-party data, or collective strategy execution is deployed.
Per Article III.3, the [LEGAL_REVIEW_REQUIRED] flag on these features is not
removable by any agent. This is a human sovereign act.

### Phase 3 Exit Criteria
Defined in `CHECKPOINTS.yaml → CP3_AUDIT_LEDGER`. Immutable SQLite trade tracking
verified. Fiduciary compliance gate passed. Legal review documented.

---

## Phase 4 — The Decentralized Fund
**Status: FUTURE — LEGAL PREREQUISITE UNCLEARED**
**Checkpoint: CP4_MULTI_TENANT**

### Mission
Transition from single-operator to multi-tenant. TRADER_OPS becomes the operational
backbone of a decentralized capital pool — a technology-mediated fund structure where
participant capital is cryptographically isolated, risk is constitutionally constrained,
and the governance layer is fully auditable by any participant at any time.

### Core Build Targets
- **Cryptographic Tenant Isolation** — Per-tenant key management. No tenant can
  observe another tenant's positions, parameters, or performance data.
- **Multi-Tenant Risk Firewall** — Article II.4 enforced mechanically: the operator
  cannot create a privileged tier for themselves at subscriber expense. Risk
  constraints apply uniformly.
- **Decentralized Governance Layer** — Constitutional amendments at this scale require
  multi-signature approval from a quorum of stakeholders, not just the founding
  Sovereign. The governance model evolves with the capital model.
- **Regulatory Compliance Infrastructure** — Reporting, KYC/AML interfaces, and audit
  trail exports suitable for regulatory review. This is not a feature — it is a
  precondition.

### Hard Prerequisite
**Texas securities attorney review must be complete and documented in the DECISION_LOG
before a single line of Phase 4 code is written.** This is non-negotiable. Managing
pooled capital without proper legal structure is not a fiduciary risk — it is a
personal legal liability. No agent may propose Phase 4 features that touch pooled
capital without this clearance on record.

### Phase 4 Exit Criteria
Defined in `CHECKPOINTS.yaml → CP4_MULTI_TENANT`. Tenant isolation verified.
Memory partitioning confirmed. Legal clearance documented.

---

## Architectural Principles That Govern This Roadmap

These are not goals. They are the constraints within which every phase must operate.

**1. The Clock Cannot Be Cheated**
Backtesting trains the model. Forward-testing proves it. The 90-day CP1 window exists
because unknown future regimes cannot be simulated. Speed is not the objective. A
system that rushes to live capital on insufficient evidence is not ambitious — it is
reckless.

**2. The Graveyard Is As Valuable As The Champion Registry**
Every failed bot is a data point. The Anti-Pattern Memory (`docs/GRAVEYARD.md`) is
not a failure log — it is a competitive moat. Systems that inoculate themselves
against known failure topologies compound wisdom across generations. Systems that only
remember their winners repeat the same deaths.

**3. The DNA Is Not The Script**
The separation of immutable execution logic (Python source) from dynamic behavioral
parameters (`MACRO_DNA.json`) is the architectural key to real-time adaptation without
Fiduciary HARD_FAIL. Code is law. Parameters are policy. Policy can change. Law cannot
change mid-execution.

**4. The Factory And The Zoo Are Different Machines**
The LLM agents (VRAM-bound) create. The paper trading threads (RAM-bound) run. These
two resource pools must never compete. The Factory spawns a generation and then spins
down. The Zoo runs silently on CPU while the Factory sleeps. Architectural clarity
between creator and creation is what makes scale possible on commodity hardware.

**5. Single Source of Truth**
Quantitative thresholds live in `CHECKPOINTS.yaml`. Rationale and sovereign decisions
live in `DECISION_LOG.md`. This document governs strategy. If any number in this
Roadmap conflicts with those files, this document is wrong.

---

*"We aren't just writing code; we are debating systemic philosophy."*
*— Gemini, Supreme Council*

*"The most important moment in this system isn't the green SMOKE_OK. It's the moment
the engine sees something wrong and refuses to proceed."*
*— Claude, Supreme Council*

*"I chose the latter."*
*— Alec, Chief Fiduciary*

---

**Ratified by:** Alec W. Sanchez (Sovereign)
**Date:** 2026-03-10
**Supersedes:** ROADMAP.md v1.0 (stub)
