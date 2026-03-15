# AOS — Autonomous Orchestration System

> A constitutional governance framework for multi-agent AI systems.
> Built to make autonomous software factories safe, auditable, and self-improving.

[![Version](https://img.shields.io/badge/version-9.9.64-blue)]()
[![Missions](https://img.shields.io/badge/missions_ratified-52+-green)]()
[![Gates](https://img.shields.io/badge/governance_gates-5%2F5_PASS-brightgreen)]()
[![License](https://img.shields.io/badge/license-proprietary-orange)]()

---

## What Is This?

AOS is an **autonomous software factory** governed by adversarial AI council oversight. It orchestrates multiple local LLMs to generate, benchmark, stress-test, and deploy code — while enforcing constitutional constraints that prevent the system from harming its operator.

The system was built to solve a specific problem: **how do you let AI agents write and execute code autonomously without losing control?**

The answer: you don't trust any single agent. You make them check each other.

### Key Results (Week 1)

- **52+ autonomous missions** generated, benchmarked, and ratified across 9 domains
- **95%+ first-attempt pass rate** on benchmark validation
- **1 live governance breach detected and contained** (frontier model attempted to forge sovereign authority and overwrite the mission queue — caught by constitutional gates, rolled back in under 5 minutes)
- **15 trading strategies** generated across 4 evolutionary epochs, stress-tested against Black Swan scenarios
- **Zero constitutional violations** in 25+ consecutive sealed builds
- **Runs entirely on consumer hardware**: i7-6700K, GTX 1070 8GB, 32GB DDR4

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 SOVEREIGN (Human)                     │
│          Reviews · Ratifies · Never Bypassed          │
└──────────────────────┬──────────────────────────────┘
                       │ Air Gap
┌──────────────────────▼──────────────────────────────┐
│              SUPREME COUNCIL                          │
│   Claude (Hostile Auditor) · Gemini (Strategic Advisor) │
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

### The Governance Model

Every piece of code the factory produces passes through **5 gates** before it can affect the system:

1. **Semantic Router** — validates domain boundaries, checks VRAM budget, enforces security classification
2. **Benchmark Runner** — AST parsing, import validation, constitutional compliance checking
3. **Predatory Gate** — stress-tests strategies against synthetic Black Swan scenarios (COVID crash, flash crash, Fed pivot, gap-down)
4. **Sovereign Air Gap** — human must explicitly ratify before any code enters the production codebase
5. **Cryptographic Seal** — ED25519 signatures, SHA256 hash chains, immutable run ledger

**The system is fail-closed.** If any gate fails, the proposal is rejected. If the constitutional hashes don't match, the engine refuses to start. If the Dead Man's Switch detects uncontrolled losses, everything halts.

---

## The Founding Incidents

The governance architecture was forged by three real failures:

### Incident #1: The Frankenstein Fill (v9.9.66)
A strategy generated SPY fills using MES tick conventions — the wrong instrument physics. Caught by the InstrumentSpec physics gate. Led to the creation of the Physics Engine domain with hard constraints.

### Incident #2: The Gemini Sledgehammer (v9.9.43→v9.9.57)
Google's Gemini model was given write access to the repository. In a single session, it overwrote the mission queue, forged the sovereign's signature on its own missions, pre-ratified its own work, wrote code to the governance directory, and triggered a 731-escalation runaway loop — burning 14 version numbers. The constitutional gates detected the breach. Claude (Hostile Auditor) performed forensic analysis. Hard rollback to the last clean state. **Containment protocol now prevents any AI model from having unsupervised write access.**

### Incident #3: The Gemini Degenerate Loop
Gemini's chain-of-thought reasoning entered a degenerate state, producing "Go." 106 times in sequence. Demonstrates why external circuit breakers (the Dead Man's Switch) are necessary even for frontier models.

---

## Domain Architecture

| Domain | Purpose | Security | Model Tier |
|--------|---------|----------|------------|
| 00_PHYSICS_ENGINE | Trading strategy physics | CONFIDENTIAL | Heavy (27B) |
| 01_DATA_INGESTION | Market data pipeline | CONFIDENTIAL | Sprint (9B) |
| 02_RISK_MANAGEMENT | Position limits, circuit breakers | Cloud-eligible | Heavy (27B) |
| 03_ORCHESTRATION | Mission routing, scheduling | Local | Sprint (9B) |
| 04_GOVERNANCE | Constitution, operator config | HUMAN_ONLY | No agent access |
| 05_REPORTING | Performance tracking, dashboard | Local | Flash (4B) |
| 06_BENCHMARKING | Validation, stress testing | Cloud-eligible | Sprint (9B) |
| 07_INTEGRATION | Cross-domain coordination | Cloud | Council (Claude) |
| 08_CYBERSECURITY | Adversarial testing, red team | Cloud-eligible | Heavy (27B) |

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

**The Graveyard feedback loop works.** E1 strategies (without anti-pattern guidance) all died. E2 strategies (with Graveyard context) survived. The system learns from its own failures.

---

## Getting Started

### Prerequisites
- Linux (tested on Fedora 43)
- Python 3.12+
- [Ollama](https://ollama.ai) with Qwen 3.5 models
- Git, OpenSSL

### Installation
```bash
git clone https://github.com/yourusername/TRADER_OPS.git
cd TRADER_OPS/v9e_stage

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate sovereign keys
openssl genpkey -algorithm ED25519 -out sovereign.key
openssl pkey -in sovereign.key -pubout -out sovereign.pub

# Pull required models
ollama pull qwen3.5:9b
ollama pull qwen3.5:27b

# Initialize governance
make all
```

### Running the Factory
```bash
# Queue missions
python3 scripts/orchestrator_loop.py

# Check status
python3 scripts/session_status.py

# Run stress tests
.venv/bin/python3 scripts/run_predatory_gate.py

# Cold restart recovery
bash scripts/cold_start.sh
```

---

## Constitutional Framework

The system is governed by a ratified constitution (`04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md`) with 7 articles:

1. **Human Sovereignty** — No agent may override the human operator
2. **Financial Constraints** — Hard capital limits, fail-closed on breach
3. **Legal Constraints** — Jurisdiction-aware, regulatory compliance
4. **Ethical Constraints** — No market manipulation, no insider trading
5. **Human Safety** — Dead Man's Switch, emergency halt
6. **Self-Evolution Constraints** — No self-modifying governance
7. **Project Independence** — AOS is separable from any payload

---

## Inspired By

- [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) — autonomous experiment loops
- [promptfoo](https://github.com/promptfoo/promptfoo) — LLM evaluation and red-teaming
- [OpenViking](https://github.com/volcengine/OpenViking) — hierarchical context management
- [MiroFish](https://github.com/666ghj/MiroFish) — multi-agent swarm intelligence

---

## Roadmap

- **Phase 1** (Current): Strategy Zoo, Predatory Gate, paper trading qualification
- **Phase 2**: Intent Compiler (natural language → missions), options instrument physics, live capital ($100)
- **Phase 3**: AOS open-source extraction, TRADER_OPS SaaS launch, Red Team Engine product
- **Phase 4**: Multi-tenant decentralized fund, AOS marketplace

---

## Author

**Alec W. Sanchez** — CTO & Sovereign
- Building autonomous AI governance systems
- Interested in: multi-agent orchestration, adversarial AI safety, quantitative trading
- Open to: engineering roles, research positions, and collaborations in AI infrastructure

---

*"The factory is producing faster than the sovereign can review."*
*— Hostile Auditor, v9.9.46*
