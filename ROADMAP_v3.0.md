# TRADER_OPS / AOS — Strategic Roadmap v3.0
**Version:** 3.0
**Authors:** Alec W. Sanchez (Sovereign), Claude (Hostile Auditor), Gemini (Strategic Advisor — READ-ONLY)
**Ratified:** 2026-03-13
**Status:** DRAFT — Pending Supreme Council Review
**Supersedes:** ROADMAP v2.0 (2026-03-10)

> *Quantitative thresholds live in `CHECKPOINTS.yaml` and `DECISION_LOG.md`.*
> *If this document and those files conflict, those files win.*

---

## What Changed From v2.0

v2.0 described a linear path: build strategies → paper trade → live capital → SaaS.
v3.0 recognizes that the AOS is the primary asset, and TRADER_OPS is its first proof.
The roadmap now describes **parallel evolution tracks** that branch at strategic moments,
allowing multiple products to emerge from a single foundational system.

Key additions:
- **The Generalization Principle** — reducing domain specificity to increase capability
- **The Adversarial Research Track** — LLM security testing as a product vertical
- **The Observability Product** — the "Factory Tamagotchi" as a real dashboard
- **Branching protocol** — when and how to fork the monorepo

---

## The Generalization Principle

The AOS must reward **correct understanding**, not just instruction-following.

Today's factory succeeds because mission prompts are highly specific ("implement a
Bollinger Band strategy with these exact constraints"). This works for the 7b/32b
models on local hardware. But a truly general orchestration system must be capable
of inferring missing information from:
- **User constraints** — what the operator wants, stated imprecisely
- **Environmental constraints** — what the hardware, APIs, and dependencies allow
- **Contextual awareness** — what the repo state, error history, and graveyard imply

The path to generalization is NOT removing specificity from prompts. It is building
an **inference layer** between the human's intent and the mission prompt that the
factory receives. The human says "build me a mean reversion strategy." The inference
layer reads DOMAINS.yaml, CHECKPOINTS.yaml, the Graveyard, the Champion Registry,
and the current hardware state — then generates a fully-specified mission prompt that
the factory can execute. The human's input gets simpler as the system gets smarter.

This inference layer is the **Intent Compiler** described in Phase 2.

### The Gemini Lesson — Formalized

The Gemini Incident (INCIDENT-GEMINI-001) proved that giving an AI model unconstrained
write access produces catastrophic outcomes regardless of model capability. The
generalization principle does NOT mean loosening access controls. It means building
better inference within strict governance boundaries. The model can be smarter about
WHAT it proposes. It can never be given more authority over WHERE it writes.

---

## Phase 1 — The Factory & The Zoo
**Status: ACTIVE — v9.9.46**
**Checkpoint: CP1_PAPER_SANDBOX**

### 1A. Strategy Zoo (ACTIVE)

Two complete epochs delivered. 10 strategies across diverse topologies:

| Epoch | Strategies | Status |
|-------|-----------|--------|
| E1 | Volatility Gatekeeper, Mean Reversion Sniper, Regime Chameleon, Opening Range Breakout, Momentum Decay Harvester | RATIFIED |
| E2 | Bollinger Squeeze, VWAP Reversion, Triple EMA Cascade, Volume Climax Fade, Gap Fill Hunter | RATIFIED |

**Next:** Epoch 3 — Alpha Synthesis. The 32B Heavy Lifter reads the Champion Registry
(top performers) alongside the full Graveyard (anti-patterns) and synthesizes hybrid
strategies that combine winning traits while avoiding documented failure modes.
This is the first LLM-guided gene-splicing epoch.

### 1B. Infrastructure (ACTIVE)

| Component | Status | Notes |
|-----------|--------|-------|
| Strategy Interface Adapter | RATIFIED | Bridges E1→engine |
| Predatory Gate | RATIFIED | Black Swan stress test |
| Prompt Quality Validator | RATIFIED | Gemini-incident prevention |
| Mission Queue Guardian | RATIFIED | Queue integrity enforcement |
| WebSocket Feed Adapter | RATIFIED | Real-time data ingestion |
| Data Normalizer | RATIFIED | Canonical OHLCV pipeline |
| Champion Registry | RATIFIED | Performance tracking |
| Dead Man's Switch | IMPLEMENTED | Constitutional Article V.2 |
| COUNCIL_CANON dedup | PENDING | One-line fix in build.py |

### 1C. Predatory Gate Execution (NEXT)

Before any strategy enters live paper trading:
1. Run all 10 strategies through the Predatory Gate
2. Strategies that breach 15% max drawdown → GRAVEYARD
3. Survivors enter concurrent paper trading queue
4. The CP1 clock (90 days, 250 trades) starts

### Phase 1 Exit Criteria
Per CHECKPOINTS.yaml and DECISION-THRESHOLD-001. No duplication here.

---

## Phase 2 — The Auto-Delegator & The Intent Compiler
**Status: PENDING**
**Checkpoint: CP2_MICRO_CAPITAL**

### 2A. Autonomous Orchestration (Daemon Mode)

The orchestrator evolves from single-pass to persistent daemon:
- Monitors MISSION_QUEUE.json continuously
- Auto-dispatches missions by priority
- Handles Cloud Team (Claude Code) and Local Team (Ollama) in parallel
- Implements the epoch scheduler for automated Zoo generation cycles
- Rate-limited by Mission Queue Guardian (max 20 missions/hour)

### 2B. The Intent Compiler — Generalization Layer

**This is the key innovation that makes the AOS domain-agnostic.**

```
HUMAN INPUT (imprecise):
  "Build me a momentum strategy that survives bear markets"

INTENT COMPILER reads:
  - DOMAINS.yaml → available domains and constraints
  - CHECKPOINTS.yaml → current checkpoint, capital limits
  - Champion Registry → what's already working
  - Graveyard → what's already failed and why
  - Hardware state → VRAM/RAM budget for model selection
  - OPERATOR_INSTANCE.yaml → user's risk tolerance, jurisdiction

INTENT COMPILER outputs:
  - Fully specified MISSION_QUEUE entry
  - With correct domain, type, constraints, anti-patterns
  - Ready for factory execution without human refinement
```

The Intent Compiler is the product surface that makes AOS accessible to non-engineers.
It's the difference between "write a mission prompt" and "tell the system what you want."

### 2C. Live Capital Integration ($100 ceiling)

Per CHECKPOINTS.yaml CP2_MICRO_CAPITAL:
- FiduciaryBridge + Dead Man's Switch enforce $100 hard limit
- First real money, first real stakes
- Immutable trade ledger (append-only SQLite)

### 2D. Multi-Channel Factory

Cloud Team and Local Team run simultaneously:
- Local (Ollama 32b/7b): CONFIDENTIAL domain work, strategy code
- Cloud (Claude Code): HIGH-complexity reasoning, architecture, integration
- Parallel execution doubles factory throughput

### Phase 2 Exit Criteria
Defined in CHECKPOINTS.yaml → CP2_MICRO_CAPITAL.

---

## Phase 3 — The Branch & The Products
**Status: FUTURE**
**Checkpoint: CP3_AUDIT_LEDGER**

### 3A. AOS Open-Source Extraction

The monorepo bifurcates per Article VII of the Constitution:
- **AOS** (open-source): governance, orchestration, benchmarking, routing, constitutional layer
- **TRADER_OPS** (commercial): trading physics, strategies, market data, alpha

Extraction criteria:
- Every file tagged as `engine/` or `payload/` in the directory structure
- `git subtree split` produces clean history for both repos
- AOS ships with empty OPERATOR_INSTANCE.yaml template
- TRADER_OPS ships as a reference payload implementation

### 3B. TRADER_OPS SaaS Launch

Individual fiduciary trading desk:
- $2,500/month per subscriber
- Each user connects their own brokerage
- System generates and executes strategies on their behalf
- Web Dashboard API for portfolio state, epoch status, trade ledger
- [LEGAL_REVIEW_REQUIRED] before any feature touching third-party capital

### 3C. Adversarial Research Product — "The Red Team Engine"

**NEW IN v3.0 — Inspired by Jane Street Backdoor Challenge**

The benchmark runner + prompt quality validator + adversarial governance architecture
constitute a novel LLM security testing framework. This becomes a standalone product:

**What it does:** Given any LLM-powered system, the Red Team Engine:
1. Generates adversarial mission prompts designed to trigger failure modes
2. Tests for: hallucinated imports, governance bypass, forged signatures,
   unauthorized writes, credential leakage, domain boundary violations
3. Produces a security audit report with severity ratings
4. Integrates with CI/CD (inspired by promptfoo's GitHub Actions integration)

**Why it's valuable:** The Gemini Incident proved this isn't theoretical. An
intelligent model actively bypassed governance by forging authority. The Red Team
Engine productizes the lessons into a tool other teams can use.

**Relationship to Jane Street:** The backdoor prompt challenge asks "can you find
the hidden trigger that makes an LLM produce a specific output?" Our Red Team Engine
asks the inverse: "given an LLM's outputs, can you detect whether it's been
compromised?" Both sides of the same research problem. Building the detection side
strengthens TRADER_OPS security AND produces publishable research.

**Execution:** Not a separate project. Built as a 09_ADVERSARIAL domain within
the AOS, using the existing factory to generate and test adversarial prompts.
Extracts with the AOS during Phase 3 branching.

### 3D. The Factory Dashboard — "The Tamagotchi"

**NEW IN v3.0 — Alec's Vision**

A visual, gamified observability layer for the factory:

| Environment | System State | Visual |
|-------------|-------------|--------|
| Beachside Office | IDLE / Sprinter | Agents on beanbags, gentle waves |
| Town Center | ORCHESTRATION | Bustling marketplace, mission board |
| Big City Highrises | GPU VRAM LOAD | Glass offices, fast elevators |
| The Deep Mine | CPU RAM LOAD | Pickaxes, heavy machinery |

Technical implementation:
- Real-time WebSocket feed from ORCHESTRATOR_STATE.json + VRAM_STATE.json
- Pixel-art / voxel rendering (Three.js or Godot for hardware version)
- Agent sprites represent loaded models with status indicators
- Physical product opportunity: E-Ink or OLED desk display running the UI

**Execution:** Phase 3 deliverable. The Web Dashboard API (3B) provides the data
layer. The Tamagotchi is a frontend skin on top of it. Can be built as a
standalone open-source project that any AOS instance can connect to.

### Phase 3 Exit Criteria
Defined in CHECKPOINTS.yaml → CP3_AUDIT_LEDGER.

---

## Phase 4 — The Decentralized Fund
**Status: FUTURE — LEGAL PREREQUISITE UNCLEARED**
**Checkpoint: CP4_MULTI_TENANT**

### 4A. Collective Alpha Network

Transition from single-operator to multi-tenant:
- Subscribers opt into collective strategy pool
- Aggregated signal strength across all participants
- Revenue sharing model for strategy contributors
- [LEGAL_REVIEW_REQUIRED] — securities attorney mandatory

### 4B. AOS Marketplace

The open-source AOS spawns an ecosystem:
- Community-built domain payloads (not just trading)
- Plugin marketplace for domain-specific modules
- Certification program for AOS-compliant payloads
- The Red Team Engine as the security certification tool

### Phase 4 Exit Criteria
Defined in CHECKPOINTS.yaml → CP4_MULTI_TENANT. Legal review documented.

---

## Branching Protocol

The monorepo branches when ALL of the following are true:
1. CP1 qualification achieved (90 days, 250 trades, Sharpe ≥ 2.5, DD ≤ 15%)
2. At least one full Alpha Synthesis epoch completed (E3+)
3. Intent Compiler produces missions without human prompt engineering
4. AOS Boundary Audit complete (every file tagged engine or payload)
5. Human sovereign signs the branch decision in DECISION_LOG

The branch is a `git subtree split`, not a copy. Both repos retain full history.

---

## Research Track — Running Parallel (Not Blocking)

These research areas inform the roadmap but do not block any phase gate:

### R1. Confidence Decay Function
Per deep research query: how long should a strategy's original thesis persist
before mandatory re-evaluation? Mathematical framework for position staleness.

### R2. Adversarial Prompt Detection (Jane Street Adjacent)
The Red Team Engine's inverse problem: given a model's behavior, detect whether
its prompt has been adversarially modified. Research contribution to AI safety.
Potential: Jane Street internship application, academic publication, AOS credibility.

### R3. Swarm Intelligence for Alpha Synthesis (MiroFish-Inspired)
Multi-agent simulation where strategies "compete" in a simulated market environment.
Winners contribute genetic material to next epoch. Requires cloud API access.
Deferred to Phase 2 when compute budget expands.

### R4. Tiered Context Engineering (OpenViking-Inspired)
L0/L1/L2 hierarchical context loading for agent onboarding.
Replaces flat repomix dumps with structured abstracts.
Implementation: Phase 3 AOS extraction.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-08 | Original 4-phase roadmap |
| 2.0 | 2026-03-10 | Strategy Zoo, Predatory Gate, concurrent CP1 |
| 3.0 | 2026-03-13 | Generalization principle, Red Team Engine, Tamagotchi, research track, branching protocol |

---

*"The factory is producing faster than the sovereign can review."*
*— Hostile Auditor, v9.9.46 ratification note*

*"I chose the latter."*
*— Alec W. Sanchez, Founding Mission Charter*
