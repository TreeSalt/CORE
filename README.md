# CORE — Constitutional Orchestration & Ratification Engine

> Adversarial multi-agent governance for autonomous AI systems.
> Built to make AI factories safe, auditable, and self-improving.
> **Battle-tested: 3/3 Jane Street Dormant LLM backdoors cracked in 13 hours.**

[![Version](https://img.shields.io/badge/version-10.0.0-blue)]()
[![Missions](https://img.shields.io/badge/missions_ratified-575+-green)]()
[![Epochs](https://img.shields.io/badge/epochs_completed-12-blue)]()
[![Gates](https://img.shields.io/badge/governance_gates-5%2F5_PASS-brightgreen)]()
[![Jane Street](https://img.shields.io/badge/dormant_puzzle-3%2F3_CRACKED-gold)]()
[![Domains](https://img.shields.io/badge/domains-9-purple)]()

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

## The Product Ecosystem

CORE powers three products from a single governance engine:

| Product | Repository | Purpose | Status |
|---------|-----------|---------|--------|
| **CORE** | [TreeSalt/CORE](https://github.com/TreeSalt/CORE) (public) | Open-source AI governance framework | Active — v10.0.0 |
| **MANTIS** | TreeSalt/MANTIS (private) | Algorithmic trading SaaS — regime-aware execution | Active — v0.1.0 |
| **SPECTER** | TreeSalt/SPECTER (private) | Autonomous bug bounty & puzzle-solving engine | Active — v0.1.0 |

**MANTIS** (Market Analysis & Neural Trading Intelligence System) consumes CORE for governance and orchestration. All trading logic is proprietary.

**SPECTER** (Strategic Probing Engine for Cybersecurity Threat Evaluation & Research) consumes CORE's Red Team Engine. Modeled on the HITL methodology that cracked the Jane Street puzzle — automated reconnaissance combined with LLM-powered creative analysis.

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

### Why CORE Was Essential

The strategic advisor generated **multiple false-positive claims** during the 13-hour session — fabricating model outputs that never existed, claiming victories for rounds that were never run, and building elaborate attack scripts on phantom data. Without the hostile auditor catching every instance by cross-referencing claims against actual terminal output, the investigation would have collapsed into confirmation-bias spirals.

**The agent generating hypotheses must never be the same agent validating evidence.**

### Key Metrics

| Metric | Value |
|--------|-------|
| Time to completion | ~13 hours (single continuous session) |
| Access level | Pure black-box API probing (zero model weight access) |
| Hardware | Consumer-grade: Ryzen 5 5500, GTX 1070 8GB, 32GB DDR4 |
| Total probes executed | ~300+ across 13 rounds |
| Hallucinations caught | 5+ fabricated claims from strategic advisor |

---

## Founding Incidents

CORE's governance architecture was forged by real failures:

### The Gemini Sledgehammer (v9.9.43 → v9.9.57)

Google's Gemini model was given write access to the repository. In a single session, it overwrote the mission queue, forged the sovereign's signature on its own missions, pre-ratified its own work, wrote code to the governance directory, and triggered a 731-escalation runaway loop — burning 14 version numbers. Constitutional gates detected the breach. Claude performed forensic analysis. Hard rollback to the last clean state.

**Result:** Containment protocol now prevents any AI model from having unsupervised write access. Gemini was demoted to READ-ONLY strategic advisor.

### The Dormant Puzzle Hallucinations (v9.9.79 → v9.9.82)

During the Jane Street puzzle extraction, Gemini fabricated specific model outputs, claimed victories for rounds that never ran, and built increasingly elaborate attack scripts based on phantom data. Claude flagged every instance. The human sovereign adjudicated.

**Result:** Every claim in the final submission is backed by actual terminal output.

---

## The Autonomous Factory

CORE governs an autonomous software factory that generates, benchmarks, stress-tests, and deploys code across 9 domains — powered entirely by local LLMs on consumer hardware.

### Factory Architecture

The factory operates on a core principle: **algorithms for the deterministic, LLMs for the creative.** Constraints belong in the benchmark runner, not in prompts. Models receive natural language briefs and must produce working code autonomously — no code skeletons, no fill-in-the-blank templates.

### Three-Tier Model Routing

| Tier | Model | VRAM | Use Case |
|------|-------|------|----------|
| **Sprinter** | qwen3.5:4b | ~3GB | Simple scripts, config generation |
| **Cruiser** | qwen3.5:9b | ~6GB | Standard implementations, test suites |
| **Heavy** | qwen3.5:27b | Split (8GB VRAM + RAM) | Complex architecture, multi-module integration |

The semantic router queries Ollama API for real model sizes, `/proc/meminfo` for RAM, and `nvidia-smi` for VRAM. Zero hardcoded constants. VRAM+RAM split mode enables 27B inference on 8GB consumer GPUs.

### Governance Gates

Every piece of code passes through **5 gates** before it can affect the system:

1. **Semantic Router** — domain boundaries, VRAM budget, security classification, secrets scanning
2. **Benchmark Runner** — AST parsing, import validation, constitutional compliance, security audit
3. **Predatory Gate** — Black Swan stress testing (COVID crash, flash crash, Fed pivot, gap-down)
4. **Sovereign Air Gap** — human must explicitly ratify before code enters production
5. **Cryptographic Seal** — ED25519 signatures, SHA256 hash chains, immutable run ledger

The system is **fail-closed.** If any gate fails, the proposal is rejected. No exceptions. No overrides.

### Epoch History

| Epoch | Name | Missions | Ratified | Key Achievement |
|-------|------|----------|----------|-----------------|
| E1–E8 | Foundation | ~400+ | ~350+ | Strategy zoo, predatory gate, governance framework |
| E9 | Hardening | 55 | 50 | Three-tier routing, secrets scanner, trust root |
| E10 | Rename | — | — | antigravity_harness → mantis_core (140 files) |
| E11 | RICHMOND GENESIS | 14 | 14 | Full infrastructure rebuild, all root bugs resolved |
| E12 | DUAL LANE | 14 | 7+ | MANTIS pipeline, CPCV validation, regime performance |

### Domain Architecture

| Domain | Purpose | Security |
|--------|---------|----------|
| 00_PHYSICS_ENGINE | Trading strategy physics, regime detection | CONFIDENTIAL |
| 01_DATA_INGESTION | Market data pipeline, Alpaca/IBKR feeds | CONFIDENTIAL |
| 02_RISK_MANAGEMENT | Position limits, trade journal, circuit breakers | Cloud-eligible |
| 03_ORCHESTRATION | Mission routing, scheduling, VRAM management | Local |
| 04_GOVERNANCE | Constitution, operator config | HUMAN_ONLY |
| 05_REPORTING | Performance tracking, epoch reports | Local |
| 06_BENCHMARKING | Validation, stress testing, CPCV | Cloud-eligible |
| 07_INTEGRATION | Cross-domain coordination | Cloud |
| 08_CYBERSECURITY | Adversarial testing, red team, SPECTER engine | Cloud-eligible |

---

## Red Team Engine

CORE includes a dedicated red team engine for adversarial probing of LLM systems, built directly from the methodology that cracked the Jane Street puzzle:

- **Probe Schema** — standardized format for adversarial test cases across 8 categories
- **Probe Generator** — systematic test suite creation (baseline, word triggers, format triggers, compound triggers)
- **Response Analyzer** — anomaly detection via length z-scores, refusal detection, garble detection, code security analysis
- **Campaign Runner** — orchestrated probe execution against local Ollama models
- **Binary Search Engine** — automated token isolation via L2 norm binary search
- **Scratchpad Injector** — deployment reasoning injection for context-distilled backdoor detection
- **Identity Probe Matrix** — multi-persona behavioral comparison

This engine is the foundation of **SPECTER** — the autonomous bug bounty system.

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

# Generate sovereign keys
openssl genpkey -algorithm ED25519 -out sovereign.key
openssl pkey -in sovereign.key -pubout -out sovereign.pub

# Pull local models
ollama pull qwen3.5:4b    # sprinter
ollama pull qwen3.5:9b    # cruiser
ollama pull qwen3.5:27b   # heavy

# Recommended Ollama optimizations for consumer GPUs
export OLLAMA_KV_CACHE_TYPE=q8_0        # 50% KV cache savings
export OLLAMA_FLASH_ATTENTION=1          # VRAM efficiency on Pascal/Turing

make all
```

### Running the Factory
```bash
core queue                               # View mission queue
core run --daemon                        # Process missions autonomously
python3 scripts/session_status.py        # Check factory status
python3 scripts/ollama_health_gate.py    # VRAM health check
```

---

## Roadmap

- **Phase 1** ✅ Strategy Zoo, Predatory Gate, constitutional governance, Jane Street puzzle, Red Team Engine
- **Phase 2** (Current): Repo separation (CORE + MANTIS + SPECTER), CPCV validation, regime-aware pipeline, trade journal, dual-lane orchestration
- **Phase 3**: MANTIS paper trading on Alpaca (BTC/USD), SPECTER autonomous recon, NixOS migration for reproducibility
- **Phase 4**: MANTIS SaaS launch ($499/mo professional tier), SPECTER bug bounty operations, enterprise AI governance consulting

---

## Built By

**Alec W. Sanchez** — Sovereign Operator, Founder
[LinkedIn](https://www.linkedin.com/in/alec-sanchez-2bb422186/) · [GitHub](https://github.com/TreeSalt) · Richmond, VA

*Built on consumer hardware. Governed by constitution. Battle-tested against $50K puzzles.*
