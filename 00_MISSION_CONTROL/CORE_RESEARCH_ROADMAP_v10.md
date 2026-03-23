# CORE Research-Informed Roadmap — v10.0.0

> **Generated:** 2026-03-23
> **Authors:** Alec Sanchez (Sovereign/CTO, TreeSalt), Claude (Hostile Auditor, Anthropic), Gemini (Strategic Research Advisor, Google DeepMind)
> **Context:** This roadmap synthesizes findings from 12 deep research papers produced by Google Gemini's Deep Research capability, 50 adversarial architectural questions answered by Claude as CORE's Hostile Auditor, and the operational results of CORE's v10.0.0 overnight epoch (50/55 missions ratified, 91% pass rate).

---

## How This Roadmap Was Built

CORE's development is guided by a multi-model adversarial methodology. Rather than relying on a single AI perspective, CORE leverages each model's strengths in a structured research-to-production pipeline:

**Google Gemini (Strategic Research Advisor — READ-ONLY):** Produced 12 comprehensive research papers via Deep Research, covering the full spectrum from quantitative epistemology to kernel-native orchestration. Gemini's role is ideation and literature synthesis — it does not modify the codebase.

**Claude (Hostile Auditor — ADVERSARIAL):** Answered 50 architectural questions designed to stress-test CORE's design philosophy, then reviewed all 12 research papers against CORE's current implementation reality. Claude's role is to distinguish what's buildable from what's aspirational, and to catch where theory outpaces engineering.

**Alec Sanchez (Sovereign — FINAL AUTHORITY):** Sets direction, resolves stalemates, ratifies all code, and bears the consequences of every decision. The constitution governs the factory; the Sovereign governs the constitution.

This adversarial triangle ensures that CORE's roadmap is neither underfunded by pessimism nor overcommitted by hype. Every item below has been pressure-tested across all three perspectives.

---

## Research Corpus Summary

| # | Paper Title | Key Concepts for CORE | Phase |
|---|-------------|----------------------|-------|
| 1 | Regime-Aware Walk-Forward Optimization in HFT | CPCV validation, Point-in-Time databases, bitemporal timestamps | 2-3 |
| 2 | Adversarial Red-Blue Dynamics & Self-Healing Code | Externalized Memory (validates current design), BlueCodeAgent constitution summarization, AlphaEvolve evolutionary coding, six documented failure modes | 2-3 |
| 3 | Dynamic Semantic Routing & Mid-Computation State Transfer | Entropy-based hallucination detection, context compaction for cloud dispatch, TOON serialization, agent memory hierarchy | 2-3 |
| 4 | Secure IPC for Adversarial Multi-Agent LLM Systems | KV cache sizing formula, BPF-LSM kernel security, TOCTOU bypass vectors | 2-4 |
| 5 | Kernel-Native AI Orchestration via eBPF | cgroups v2 memory limits, cudaMalloc uprobes, sched_switch energy attribution, hardware watchdog timers | 2-3 |
| 6 | Zero-Trust Software Supply Chains for AI Developers | Agentic Trust Framework maturity levels, llmsa prompt attestation, Sigstore keyless signing, SPIFFE workload identity | 2-4 |
| 7 | Energy-Aware Compute Orchestration in Edge Clusters | Three-tier hardware hierarchy, sticky offloading with hysteresis, proactive checkpointing, stateless inference design | 3-5 |
| 8 | AI-Native Linux: Replacing Init with LLM Orchestration | Unified Kernel Images, neural schedulers (SchedCP, OS-R1), semantic memory tiers, deterministic supervisor patterns | 4-5 |
| 9 | Formal Verification & Sandbox Execution in Quant Finance | Proof-Carrying Code, APOLLO (LLM + Lean collaboration), Imandra for financial logic, constrained decoding via DPDA | 3-4 |
| 10 | Autonomous Python Code Generation & Dynamic Runtime | PEP 734 sub-interpreters, state bleed prevention, circular dependency guards, Service Provider Interface pattern | 2-3 |
| 11 | Multi-Agent Adversarial Networks & Game Theory for Alpha | Nash equilibrium convergence, DAG-aware factor discovery (AlphaPROBE), emergent risk-aversion, oscillation detection | 3-4 |
| 12 | Autonomous Immutable Infrastructure with NixOS | Purely functional OS, impermanence architecture, atomic rollbacks, package hallucination defense, content-addressed derivations | 3-4 |

---

## What Changed: Revised Positions After Research

The research corpus forced several concrete revisions to CORE's architectural assumptions. Intellectual honesty demands documenting these explicitly.

### 1. Walk-Forward Validation → CPCV (Paper 1)

**Previous position:** Standard walk-forward optimization is sufficient for strategy validation.

**Revised position:** CPCV (Combinatorial Purged Cross-Validation) is structurally superior. Standard WFO produces a single historical path with no variance estimate. CPCV generates multiple independent out-of-sample paths from the same dataset, allowing computation of Sharpe ratio variance — the difference between "Sharpe = 2.0" and "Sharpe = 2.0 ± 0.8." The purging and embargoing mechanisms eliminate the information leakage that makes K-fold invalid for time series.

**Action:** Implement CPCV in MANTIS's walk-forward validator as a Phase 2 mission.

### 2. Ansible Playbook → NixOS Flake (Papers 8, 12)

**Previous position (after Paper 8):** Build a Fedora Ansible playbook for CORE installation. A custom distro is too ambitious.

**Revised position (after Paper 12):** Ansible is imperative and drift-prone. NixOS provides mathematically deterministic environments with atomic rollbacks and cryptographic verification. The "impermanence" architecture (ephemeral root, persistent data whitelisted) mirrors CORE's Externalized Memory pattern at the OS level. A NixOS flake in the repo root is the production-grade path — not a custom distro, but a single declarative file that reproduces the entire CORE development environment.

**Action:** Create `flake.nix` in repo root as a Phase 3 deliverable. Full NixOS migration after MANTIS generates revenue.

### 3. Blind Retry → Oscillation Detection (Paper 11)

**Previous position:** Failed missions retry with corrective context up to max_retries.

**Revised position:** When the same gate rejects the same mission 3+ times in a row, the system is in rotational divergence — oscillating, not converging. This was demonstrated live when the credential scanner rejected crypto missions 4 consecutive times. The fix isn't "try harder with the same approach" — it's "change the incentive structure." The run loop must detect oscillation patterns (same gate, same failure class) and escalate with a structural recommendation (different model tier, different mission framing) rather than blind retry.

**Action:** Add oscillation detection to run_loop.py as a Phase 2 mission.

### 4. Python Allowlist → Kernel-Level Security (Papers 4, 5)

**Previous position:** Secure bash execution via Python-level command allowlists.

**Revised position:** BPF-LSM hooks enforce access control at Ring 0 — below the application layer, immune to Python-level bypasses. cgroups v2 memory limits provide immediate protection against Ollama VRAM spikes. eBPF uprobes on cudaMalloc would give real-time VRAM allocation visibility. The Python allowlist is a pragmatic start; the kernel-level approach is the target architecture.

**Action:** Configure cgroups v2 for Ollama immediately. Investigate eBPF integration in Phase 3.

### 5. Post-Hoc Benchmarking → Mission Preflight Gate (Paper 10 + operational experience)

**Previous position:** The benchmark runner validates proposals after generation.

**Revised position:** Catching problems after 10 minutes of inference wastes the entire VRAM budget for that attempt. Deterministic pre-flight checks (regex pattern scanning, deliverable path validation, token count estimation, dependency graph checking) should run before the router loads a model. Cost of pre-flight: milliseconds. Cost of post-inference rejection: 10 minutes of GPU time.

**Core Principle Established:** "Algorithms for the deterministic, LLMs for the creative."

**Action:** Implement `scripts/mission_preflight.py` as a Phase 2 mission. Integrate into run_loop.py dispatch path.

### 6. Static Credential Scanning → Smart Pattern Matching (Operational experience)

**Previous position:** Reject any code containing sensitive token names (api_key, password, etc.).

**Revised position:** A crypto exchange adapter *must* handle API keys by definition. The scanner must distinguish between interface declarations (`def connect(api_key: str = "")`) and hardcoded secrets (`api_key = "sk-live-abc123"`). The smart pattern matcher uses Python's tokenizer to check: is the sensitive NAME followed by `=` followed by a non-empty STRING literal? Declarations with empty defaults or variable references pass; hardcoded values fail.

**Action:** Implemented in v10.0.0. Benchmark runner credential gate upgraded.

---

## Phase 2: Hardening the Factory (Current → Next 2 Epochs)

These items address gaps exposed by the overnight epoch and validated by the research.

| Component | Paper(s) | Description | Priority |
|-----------|----------|-------------|----------|
| Mission Preflight Gate | 10, operational | Deterministic pre-screening: regex, path validation, token budget estimation | CRITICAL |
| cgroups v2 for Ollama | 5 | Set memory.high (soft throttle) and memory.max (hard limit) on Ollama process | CRITICAL |
| Oscillation Detector | 11 | Track per-gate failure patterns across retries; escalate on 3+ same-gate failures | HIGH |
| Predictive VRAM Gate | 4, 5 | KV cache sizing formula in select_tier() — predict OOM before model loads | HIGH |
| Hysteresis in Tier Selection | 7 | Don't retry Heavy tier until VRAM has been above threshold for N minutes | MEDIUM |
| Periodic Git Commit in Factory | 7 | Incremental commits during overnight runs to prevent data loss on crash | MEDIUM |
| Circular Dependency Guard | 10 | Mission template constraint: shared utils in leaf modules, no cross-domain imports | MEDIUM |
| Strategy DAG | 11 | Track strategy lineage in STRATEGY_DAG.json to prevent redundant factor discovery | LOW |

## Phase 3: Production Infrastructure (After MANTIS Paper Trading)

| Component | Paper(s) | Description | Priority |
|-----------|----------|-------------|----------|
| CPCV Validation Engine | 1 | Combinatorial Purged Cross-Validation with purging and embargoing for MANTIS strategies | CRITICAL |
| ATF Trust Maturity Levels | 6 | Intern → Junior → Senior → Principal trust escalation in OPERATOR_INSTANCE.yaml | HIGH |
| Context Compaction for Cloud Dispatch | 3 | XML-structured handoff with semantic compression when local model fails | HIGH |
| NixOS Development Flake | 12 | flake.nix declaring Python 3.14, Ollama, all deps with hashes, cgroup config | HIGH |
| Prompt Attestation (llmsa) | 6 | Hash cognitive inputs (system prompt, temperature, context) alongside code outputs | MEDIUM |
| Entropy-Based Generation Abort | 3 | Monitor streaming output entropy; abort early if model enters hallucination spiral | MEDIUM |
| Hardware Watchdog Timer | 5 | /dev/watchdog for unattended overnight runs — hard reboot on total system hang | MEDIUM |
| CORE Installation Playbook | 12 | Until NixOS migration: Ansible/Kickstart for fresh Fedora → CORE-ready in one command | MEDIUM |
| Socratic Amphitheater v1 | Gemini conversation | Turn-based multi-model debate with type-tagged messages and priority preemption | LOW |

## Phase 4: Scaling and Formal Methods (Requires Revenue/Hardware)

| Component | Paper(s) | Description | Priority |
|-----------|----------|-------------|----------|
| Formal Verification with Lean | 9 | APOLLO-style LLM + theorem prover for trading strategy invariant proofs | HIGH |
| eBPF cudaMalloc Probes | 5 | Real-time VRAM allocation visibility at kernel level | MEDIUM |
| Sub-Interpreter Benchmark Execution | 10 | PEP 734 isolated execution for proposals — zero state bleed between benchmarks | MEDIUM |
| Sigstore Keyless Signing | 6 | Replace governor seal with ephemeral X.509 certificate signing via Fulcio/Rekor | MEDIUM |
| BPF-LSM Security Enclaves | 4 | Kernel-level access control for factory processes — beyond Python allowlists | LOW |
| MARL Adversarial Training | 11 | Full multi-agent reinforcement learning for strategy generation (requires multi-GPU) | LOW |

## Phase 5: Compute Sovereignty (Long-Term Vision)

| Component | Paper(s) | Description | Priority |
|-----------|----------|-------------|----------|
| NixOS Full Migration | 12 | Impermanence architecture, atomic rollbacks, zero-drift OS for CORE hardware | HIGH |
| Off-Grid Power Integration | 5, 7 | Solar/battery telemetry via IIO subsystem, energy-aware tier degradation | MEDIUM |
| Three-Tier Hardware Cluster | 7 | GTX 1070 (Heavy) + Raspberry Pi (Light) + ESP32 (Leaf) federated under KubeEdge | MEDIUM |
| AI-Native Linux Research | 8 | UKI boot, neural schedulers, eBPF-driven kernel intelligence — academic contribution | LOW |
| IPFS Binary Cache | 12 | Decentralized artifact distribution for multi-node CORE deployments | LOW |
| AI-Native Fedora Spin | 8, 12 | The long-term dream: a NixOS-style functional layer on Fedora with CORE pre-installed | ASPIRATIONAL |

---

## Design Principles (Established Through Research)

These principles were crystallized through the 50-question adversarial dialogue and the 12-paper review.

1. **Algorithms for the deterministic, LLMs for the creative.** Pre-flight gates, pattern scanners, and resource checks are deterministic. Strategy generation, code writing, and evolution mandates are creative. Never use an LLM where a regex suffices.

2. **Externalized Memory over internal state.** Agents are stateless. All truth lives in files on disk. Recovery is a restart, not a state restoration. (Papers 2, 3, 7, 12)

3. **Fail closed, not fail open.** The worst case is flat (no position, no action). Never degrade into unverified operation. (Papers 1, 6, 9)

4. **The constitution governs the factory. The Sovereign governs the constitution.** No agent rewrites governance. The Sovereign amends governance explicitly, with a signed DECISION_LOG entry. (Papers 6, 9, 11)

5. **Predict, don't poll.** The VRAM gate should predict OOM before it happens. The power monitor should anticipate brownouts. The entropy tracker should detect hallucination mid-generation. Reactive systems arrive too late. (Papers 3, 5, 7)

6. **Defense in depth.** The kernel handles hardware safety. CORE handles application safety. Neither layer trusts the other to be sufficient. (Papers 4, 5, 8)

7. **Oscillation is not convergence.** If the same gate rejects the same mission three times, the system is diverging. Change the approach, don't increase the retry count. (Paper 11)

8. **Build for production, never lie.** Every metric is honest. Every failure is logged. Every limitation is documented. The Australian data scientist should see the same system we debug at 3 AM.

---

## Operational Results: v10.0.0 Epoch

**First Pass:** 47/55 missions ratified (85%)
**After Retries:** 50/55 ratified (91%)
**Remaining Escalations:** 5 crypto data modules — deferred to Cruiser tier (model capability limitation, not infrastructure failure)

**Root Causes Identified:**
- 5 missions: Benchmark credential scanner false positives on trigger words in mission briefs and model output → Fixed with smart pattern matching
- 2 missions: Router FAIL-CLOSED due to VRAM pressure after 37+ consecutive missions → Validates need for predictive VRAM gate
- 1 mission: Undocumented endpoint detection on mock IP addresses → Fixed with cleaner mission briefs

**Infrastructure Fixes Deployed:**
- Smart credential scanner (distinguishes declarations from hardcoded values)
- Mission preflight gate script (deterministic pre-screening)
- Cleaned mission brief templates (zero scanner trigger words)

---

*This roadmap is a living document. It will be updated after each epoch with operational results, revised positions, and new research findings. The adversarial triangle (Gemini research → Claude audit → Sovereign ratification) ensures continuous pressure-testing of every architectural decision.*
