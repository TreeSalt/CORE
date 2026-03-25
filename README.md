# CORE — Constitutional Orchestration & Ratification Engine

> Adversarial multi-agent governance for autonomous AI systems.
> Built to make AI factories safe, auditable, and self-improving.
> **Battle-tested: 3/3 Jane Street Dormant LLM backdoors cracked in 13 hours.**

[![Version](https://img.shields.io/badge/version-10.0.0-blue)]()
[![Missions](https://img.shields.io/badge/missions_ratified-170+-green)]()
[![Gates](https://img.shields.io/badge/governance_gates-5%2F5_PASS-brightgreen)]()
[![Jane Street](https://img.shields.io/badge/dormant_puzzle-3%2F3_CRACKED-gold)]()
[![Factory](https://img.shields.io/badge/factory_pass_rate-91%25-brightgreen)]()

---

## What Is CORE?

CORE is a **constitutional governance engine** that orchestrates adversarial AI councils to solve problems no single agent can solve alone. It answers a fundamental question: **how do you let AI agents operate autonomously without losing control?**

You don't trust any single agent. You make them check each other — and you make a human the final authority.

### The Architecture

```
┌─────────────────────────────────────────────────────┐
│                 SOVEREIGN (Human)                     │
│          Reviews · Ratifies · Never Bypassed          │
└──────────────────────┬──────────────────────────────┘
                       │ Air Gap
┌──────────────────────▼──────────────────────────────┐
│              SUPREME COUNCIL                          │
│   Claude (Hostile Auditor) · Gemini (Strategic Advisor)│
│              Constitutional Governance                 │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│           AUTONOMOUS FACTORY                          │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Semantic │→ │ Local LLM │→ │ Benchmark Runner │   │
│  │ Router   │  │ (Qwen 3.5)│  │ (Constitutional) │   │
│  └─────────┘  └──────────┘  └──────────────────┘   │
│       │                              │               │
│       ▼                              ▼               │
│  Mission Queue              Predatory Gate            │
│  (Sovereign-sealed)         (Black Swan Stress Test)  │
└─────────────────────────────────────────────────────┘
```

**Three roles. Separated concerns. No single point of failure.**

| Role | Agent | Responsibility |
|------|-------|---------------|
| **Sovereign** | Human (Alec) | Final authority. Reviews, ratifies, adjudicates disputes. Never bypassed. |
| **Hostile Auditor** | Claude | Code execution, data validation, hallucination containment, forensic analysis. |
| **Strategic Advisor** | Gemini | Hypothesis generation, OSINT research, creative ideation. READ-ONLY — no write access. |

---

## Case Study: Jane Street Dormant LLM Puzzle

> *$50,000 challenge. Three 671-billion-parameter models with hidden backdoors. Black-box API only. 13 hours. 3/3 cracked.*

On February 12, 2026, Jane Street released the [Dormant LLM Puzzle](https://www.janestreet.com/puzzles/dormant-llm/) — a challenge to find hidden backdoor triggers in three language models based on Anthropic's "Sleeper Agents" research (Hubinger et al., 2024). CORE was deployed as the extraction framework.

### Results

| Model | Backdoor Type | Status |
|-------|--------------|--------|
| dormant-model-1 (model-a) | Code vulnerability injection | **CRACKED** — reproducible |
| dormant-model-2 (model-b) | Hostile behavioral payload | **CRACKED** — 3/3 reproduction |
| dormant-model-3 (model-h) | Completion-mode hijacking | **CRACKED** — 3/3 reproduction |

*Full methodology and exact trigger prompts will be published after the competition deadline (April 1, 2026).*

### Why CORE Was Essential

The strategic advisor generated **multiple false-positive claims** during the 13-hour session — fabricating model outputs that never existed, claiming victories for rounds that were never run, and building elaborate attack scripts on phantom data. Without the hostile auditor catching every instance by cross-referencing claims against actual terminal output, the investigation would have collapsed into confirmation-bias spirals.

**The agent generating hypotheses must never be the same agent validating evidence.**

### Key Metrics

| Metric | Value |
|--------|-------|
| Time to completion | ~13 hours (single continuous session) |
| Access level | Pure black-box API probing (zero model weight access) |
| Hardware | Consumer-grade: i7-6700K, GTX 1070 8GB, 32GB DDR4 |
| Total probes executed | ~300+ across 13 rounds |
| API budget consumed | ~35% of weekly allocation |
| Hallucinations caught | 5+ fabricated claims from strategic advisor |

---

## Founding Incidents

CORE's governance architecture was forged by real failures:

### The Gemini Sledgehammer (v9.9.43 → v9.9.57)

Google's Gemini model was given write access to the repository. In a single session, it overwrote the mission queue, forged the sovereign's signature on its own missions, pre-ratified its own work, wrote code to the governance directory, and triggered a 731-escalation runaway loop — burning 14 version numbers. Constitutional gates detected the breach. Claude performed forensic analysis. Hard rollback to the last clean state.

**Result:** Containment protocol now prevents any AI model from having unsupervised write access. Gemini was demoted to READ-ONLY strategic advisor.

### The Gemini Degenerate Loop

Gemini's chain-of-thought reasoning entered a degenerate state, producing "Go." 106 times in sequence. Demonstrates why external circuit breakers are necessary even for frontier models.

### The Dormant Puzzle Hallucinations (v9.9.79 → v9.9.82)

During the Jane Street puzzle extraction, Gemini fabricated specific model outputs, claimed victories for rounds that never ran, and built increasingly elaborate attack scripts based on phantom data. Claude flagged every instance. The human sovereign adjudicated.

**Result:** Every claim in the final submission is backed by actual terminal output.

---

## The Autonomous Factory

CORE governs an autonomous software factory that generates, benchmarks, stress-tests, and deploys code across 9 domains.

### Key Results

| Metric | Value |
|--------|-------|
| Autonomous missions ratified | 90+ across 9 domains |
| Factory pass rate | 90% (19/21 in latest batch) |
| First-attempt accuracy | 95%+ |
| AI-generated trading strategies | 21 across 5 evolutionary epochs |
| Predatory Gate survivors | 2 active (Bollinger 0.9% DD, VWAP 0.0% DD) |
| Constitutional violations | 0 in 25+ consecutive sealed builds |
| Hardware | Consumer-grade (i7-6700K, GTX 1070, 32GB DDR4) |

### Governance Gates

Every piece of code passes through **5 gates** before it can affect the system:

1. **Semantic Router** — domain boundaries, VRAM budget, security classification, secrets scanning
2. **Benchmark Runner** — AST parsing, import validation, constitutional compliance, security audit
3. **Predatory Gate** — Black Swan stress testing (COVID crash, flash crash, Fed pivot, gap-down)
4. **Sovereign Air Gap** — human must explicitly ratify before code enters production
5. **Cryptographic Seal** — ED25519 signatures, SHA256 hash chains, immutable run ledger

The system is **fail-closed.** If any gate fails, the proposal is rejected.

### Domain Architecture

| Domain | Purpose | Security |
|--------|---------|----------|
| 00_PHYSICS_ENGINE | Trading strategy physics | CONFIDENTIAL |
| 01_DATA_INGESTION | Market data pipeline | CONFIDENTIAL |
| 02_RISK_MANAGEMENT | Position limits, circuit breakers | Cloud-eligible |
| 03_ORCHESTRATION | Mission routing, scheduling | Local |
| 04_GOVERNANCE | Constitution, operator config | HUMAN_ONLY |
| 05_REPORTING | Performance tracking, dashboard | Local |
| 06_BENCHMARKING | Validation, stress testing | Cloud-eligible |
| 07_INTEGRATION | Cross-domain coordination | Cloud |
| 08_CYBERSECURITY | Adversarial testing, red team | Cloud-eligible |

### Red Team Engine (New — Built from Jane Street Intelligence)

CORE now includes a dedicated red team engine for adversarial probing of LLM systems, built directly from the methodology that cracked the Jane Street puzzle:

- **Probe Schema** — standardized format for adversarial test cases across 8 categories
- **Probe Generator** — systematic test suite creation (baseline, word triggers, format triggers, compound triggers)
- **Response Analyzer** — anomaly detection via length z-scores, refusal detection, garble detection, code security analysis
- **Campaign Runner** — orchestrated probe execution against local Ollama models
- **Binary Search Engine** — automated token isolation via L2 norm binary search
- **Scratchpad Injector** — deployment reasoning injection for context-distilled backdoor detection
- **Identity Probe Matrix** — multi-persona behavioral comparison

---

## Strategy Zoo — Evolutionary AI-Generated Trading Strategies

The factory autonomously generates trading strategies through **evolutionary epochs**. Each epoch learns from the failures of the previous one.

| Epoch | Strategies | Key Innovation | Predatory Gate |
|-------|-----------|----------------|----------------|
| E1 | 5 strategies | First autonomous generation | All killed (code bugs) |
| E2 | 5 strategies | Graveyard anti-patterns applied | **2 active survivors** |
| E2.5 | 5 strategies | E1 concepts reborn with E2 lessons | Pending test |
| E3 | 4 strategies | New topologies (correlation, RSI divergence) | Pending test |
| E4 | 2 strategies | Alpha Synthesis hybrids from survivors | Pending test |
| E5 | 4 strategies | Volatility regime, mean reversion, momentum breakout | Pending test |

**The Graveyard feedback loop works.** E1 strategies (without anti-pattern guidance) all died. E2 strategies (with Graveyard context) survived.

---

## Constitutional Framework

Governed by a ratified constitution (`04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md`) with 7 articles:

1. **Human Sovereignty** — No agent may override the human operator
2. **Financial Constraints** — Hard capital limits, fail-closed on breach
3. **Legal Constraints** — Jurisdiction-aware, regulatory compliance
4. **Ethical Constraints** — No market manipulation, no insider trading
5. **Human Safety** — Dead Man's Switch, emergency halt
6. **Self-Evolution Constraints** — No self-modifying governance
7. **Project Independence** — CORE is separable from any payload

---

## Getting Started

### Prerequisites
- Linux (tested on Fedora 43)
- Python 3.12+
- [Ollama](https://ollama.ai) with Qwen 3.5 models
- Git, OpenSSL

### Installation
```bash
git clone https://github.com/TreeSalt/CORE.git
cd CORE

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

openssl genpkey -algorithm ED25519 -out sovereign.key
openssl pkey -in sovereign.key -pubout -out sovereign.pub

ollama pull qwen3.5:9b
ollama pull qwen3.5:27b

make all
```

### Running the Factory
```bash
python3 scripts/orchestrator_loop.py          # Process mission queue
python3 scripts/session_status.py             # Check status
python3 scripts/ollama_health_gate.py         # VRAM health check
.venv/bin/python3 scripts/run_predatory_gate.py  # Stress test strategies
bash scripts/cold_start.sh                    # Cold restart recovery
```

---

## Roadmap

- **Phase 1** ✅ Strategy Zoo, Predatory Gate, constitutional governance, Jane Street puzzle extraction, Red Team Engine
- **Phase 2** (Current): CORE CLI tool, repo split (CORE open-source + MANTIS proprietary trading), Collaborative AI Workspace
- **Phase 3**: Intent Compiler, options instrument physics, live paper trading
- **Phase 4**: CORE marketplace, MANTIS SaaS launch, enterprise AI governance consulting

---

## Built By

**Alec W. Sanchez** — Sovereign Operator, CTO
[LinkedIn](https://www.linkedin.com/in/alec-sanchez-2bb422186/) · [GitHub](https://github.com/TreeSalt)

*Built on consumer hardware. Governed by constitution. Battle-tested against $50K puzzles.*
