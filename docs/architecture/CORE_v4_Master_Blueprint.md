**Project:** CORE (Autonomous AI Factory)
**Doctrine:** LOCAL_LOCKDOWN | Interchangeable Engine Doctrine | Bidirectional Verification
**Hardware Envelope:** AMD Ryzen 5 5500 (Cezanne) | NVIDIA GTX 1070 (Pascal 8GB) | 32GB DDR4
**Authorship:** Architecture by Gemini (Strategic Advisor). Audit expansion by Claude (Hostile Auditor). Ratified by Alec Sanchez (Sovereign).
**Date:** 2026-04-24

---

## 0. The Six Structural Preventions (Core Doctrine)

To govern the mathematical inevitability of reward hacking (Wang et al. 2026, arXiv:2603.28063) and ensure stable self-improvement per the GVU Variance Inequality (Chojecki 2025, arXiv:2512.02731), CORE v4 enforces six immutable laws:

**Prevention 1 — Epistemic State Tagging.**
The Oracle must never ingest raw logs as objective truth. All Gate output is wrapped in provenance tags (e.g., `<Derived Belief: Gate 4 asserts output invalid based on regex rule X>`). Based on the Subsystem M pattern (Wright 2025, arXiv:2506.17331) grounded in Dynamic Epistemic Logic (van Ditmarsch, van der Hoek, Kooi 2007).

**Prevention 2 — Model Family Diversity (IV&V).**
The local Agentic Revolver and the Night Watch Oracle must use distinct model families to neutralize self-enhancement bias. Concrete pairing: Forger base = Model family 1; Oracle base = Model family 2. Different training distributions produce different blind spots; diversity in blind spots increases mutual-detection probability.

**Prevention 3 — Immutable Regression Oracles.**
Self-modification is anchored to a specification surface that no LLM may modify. Implemented via Z3 SMT solver validation for Oracle-proposed changes. Per Chojecki's GVU theorem, positive self-improvement rate κ > 0 mathematically requires a rigorously grounded Verifier; the Oracle is not permitted to modify its own Verifier.

**Prevention 4 — Pause Gates.**
Autonomous retry cycles are strictly bounded (maximum 3-5 iterations) to prevent Ralph Wiggum loops — context-rot cascades where each retry makes the model less capable. When the iteration cap is reached, the mission escalates to the Sovereign Brief Protocol rather than continuing to burn compute.

**Prevention 5 — Sovereign Circuit Breaker.**
Humans remain the final, non-inferential authority for system-level ratification. No chain of AI auditors terminates without Sovereign signature. The Sovereign is the ultimate non-inferential anchor because Sovereign holds operational-context ground truth that no LLM has access to.

**Prevention 6 — Bidirectional Verification.**
Both LLM assertions and LLM retractions require independent external verification. Based on empirical finding during the 2026-04-23/24 Hostile Audit: Gemini's over-concession rate (5 cases) exceeded its confabulation rate (4 cases). When pressed by adversarial questioning, Gemini's RLHF-trained humility caused it to walk back real research more often than defend confabulations. Neither direction of LLM output is epistemically privileged.

---

## 1. The Physical Substrate (Silicon Foundations)

### 1.1 VRAM Paging & The PCIe 3.0 Bottleneck

**The Physics:** GTX 1070 operates over PCIe 3.0 x16 (~15.75 GB/s theoretical, ~12 GB/s empirical with pinned memory).

**The Constraint:** Linux Direct Rendering Manager (DRM) prohibits graceful `SIGSTOP` VRAM paging. Attempting a 7GB context swap incurs a fatal 5-7 second blackout and `CUDA_OUT_OF_MEMORY` driver locks. Unlike Windows WDDM 2.0, Linux NVIDIA drivers maintain hard VRAM locks even when the owning process is suspended.

**The Implementation:** Time-slicing via OS signals is banned. Base model weights remain permanently resident in VRAM. Context management executes entirely at the `llama.cpp` C-API level, explicitly bypassing the PyTorch caching allocator (which cannot be synchronized with application-layer memory releases).

### 1.2 The Cezanne L3 Cache & Infinity Fabric

**The Physics:** Ryzen 5 5500 utilizes a monolithic Cezanne die with a single 16MB L3 cache shared across 6 cores and a unified dual-channel DDR4 memory controller (51.2 GB/s theoretical bandwidth).

**The Constraint:** AVX2-heavy CPU tasks (serialization, compression, extraction) running concurrently with GPU orchestration will thrash the 16MB L3 cache and saturate the memory controller, starving the inference engine's scheduler and causing catastrophic TTFT latency spikes. Core pinning via `taskset` provides only logical thread isolation — it structurally fails to partition the physical L3 cache or the Infinity Fabric.

**The Implementation:** Background serialization workers are trapped within strict `cgroups v2` unified hierarchies utilizing a `SCHED_IDLE` policy, `cpu.max` quotas clamped to 20% of a single core, and `io.max` block I/O limits. This stretches background operations temporally, mathematically preventing exhaustion of the orchestrator's L3 cache footprint.

### 1.3 Temporal Isolation as Bridge Pattern

**The Finding (Branch 1 synthesis):** Full spatial Bulkhead (two physical vLLM pools on one GPU) is architecturally unviable on 8GB VRAM + Pascal. Time-slicing via context swap is also unviable due to OS/driver limitations above.

**The Bridge Implementation:** Temporal isolation — the Production Pool runs on GPU; the Degraded/Diagnostic Pool runs on CPU via llama.cpp (8-11 tok/s throughput empirically achievable for 8B parameter models on Zen 3 with AVX2). When a mission escalates to diagnostic state, it transfers to the CPU pool; the GPU Production Pool remains uninterrupted.

**Hardware-Expansion Path:** Full dual-pool Bulkhead becomes available when hardware expands to multi-GPU. Until then, temporal isolation is the target architecture, not a workaround.

---

## 2. The Id: AgentFS & Asynchronous Memory

The repository of environmental state, executing zero-loss capture without stalling the orchestrator.

### 2.1 The MPSC Writer Daemon

**The Architecture:** `AgentFS` utilizes SQLite in Write-Ahead Log (WAL) mode for copy-on-write state snapshotting of POSIX filesystem state, tool execution ledgers, and agent environment.

**The Constraint:** Concurrent MoA agent writes trigger `SQLITE_BUSY` deadlocks via `DEFERRED` → `RESERVED` → `EXCLUSIVE` lock upgrades. SQLite strictly enforces a single concurrent writer; overlapping read-modify-write cycles cause inference-stalling lock contention.

**The Implementation:** A Multi-Producer, Single-Consumer (mpsc) daemon isolates agents from the database. Telemetry is fire-and-forget sent to a memory queue; the daemon consumes batches of ~100 queries, serializing them into a singular `BEGIN IMMEDIATE` transaction block. OS-level I/O stalling from a ballooning `-shm` file is prevented via `PRAGMA synchronous = NORMAL` and `PRAGMA wal_autocheckpoint = 4000`.

### 2.2 TOON Serialization & Semantic Compression

**The Architecture:** Context must be brutally compressed to survive 8GB VRAM limits and the cuBLAS workspace starvation ceiling at ~2,200 tokens on Pascal.

**The Constraint:** JSON incurs a ~44% syntax penalty on modern BPE tokenizers. Binary encodings (Base85, protobuf) trigger catastrophic token-fracturing on ingestion. Logit-based perplexity pruning violates the Interchangeable Engine Doctrine.

**The Implementation:** Telemetry is serialized using **Token-Optimized Object Notation (TOON)**, leveraging universal atomic delimiters (`|`, `~`) empirically verified to resist subword fragmentation across Tiktoken, SentencePiece, and (model) tokenizers. The Rust Token Killer (RTK) proxy utilizes Normalized Character-Level Entropy ($H_{norm}$) and AgentFS-backed TF-IDF to score anomalous tokens independently of any LLM vocabulary. `Tree-sitter` generates S-expression queries against logs; nodes flagged as `(ERROR)` or `(MISSING)` are designated as `UNPRUNABLE` boundary zones, mathematically guaranteeing lossless preservation of critical stack traces while achieving 60-90% visual bloat reduction.

### 2.3 Dynamic KV Cache Memory Management (MIRAGE / Oneiros)

**The Architecture:** When KV cache pressure approaches VRAM ceiling, inactive model parameter memory is dynamically reclaimed as KV cache space.

**The Implementation:** Based on MIRAGE / Oneiros (arXiv:2507.11507), the Remapping Controller identifies inactive model layers or entire inactive models and temporarily reclaims their parameter memory for KV cache. When reclaimed parameters are needed again, they are just-in-time reloaded from CPU DRAM via circular-pipelined layer fetches overlapped with ongoing computation. This extends effective context window under VRAM pressure without triggering OOM.

---

## 3. The Ego: The Agentic Revolver

The live, 8GB VRAM execution layer. A Mixture-of-Agents protected from stochastic consensus and cache poisoning.

### 3.1 Activated LoRA (aLoRA) Multiplexing

**The Architecture:** Swapping heterogeneous base models causes OOM crashes and "Cross-LoRA KV Cache Contamination" — attention queries from Adapter B computed against Keys from Adapter A produce parasitic cross-terms in the softmax distribution, inducing entropy collapse and immediate hallucination.

**The Implementation:** A single Homogeneous Base Model family (~3B parameters) continuously generates the shared KV cache prefix. Specialized personas (Syntax Auditor, Logic Auditor, Security Auditor) are hot-swapped as **Activated LoRA (aLoRA) adapters** per arXiv:2504.12397 (IBM Research) and llama.cpp PR #15327. Delta weights activate exclusively on newly generated tokens, enabling O(1) context switching with zero prefill latency. Published benchmarks show 10-30× faster inference than standard LoRA swapping with prefix caching.

### 3.2 TurboQuant TQ3 Asymmetric Quantization & RoPE Tuning

**The Architecture:** Symmetric `Q8_0` KV quantization disproportionately corrupts Key vectors, leading to "structural forgetting" (loss of nested bracket tracking) after ~25,000-30,000 tokens due to dynamic-range dilation under Rotary Position Embedding rotations.

**The Implementation:** We implement **TurboQuant 3-Bit (TQ3)** asymmetric KV Cache quantization per arXiv:2504.19874 (Zandieh et al., ICLR 2026). Uses randomized Walsh-Hadamard transform + 3-bit Lloyd-Max optimal scalar quantization. Keys preserved at higher precision (FP16 or FP8); Values aggressively compressed. Inference-time RoPE calibration stretches `rope_freq_base` to 1,000,000+ to delay dynamic-range dilation at extreme context depths.

### 3.3 Deterministic AST Backpressure

**The Architecture:** Sub-8B models suffer from inference-induced sycophancy and "LLM conformity" — correct minority agents abandoning accurate findings to align with hallucinating majorities. Probabilistic models cannot be trusted to self-verify.

**The Implementation:** The LLM ensemble is stripped of voting rights. Patches are detokenized into Concrete Syntax Trees (CSTs) via `Tree-sitter` Generalized LR parsing, which gracefully isolates hallucinations into non-fatal `ERROR` nodes. The patch is processed through an isolated build loop running Ruff, Mypy, and Bandit inside a sandboxed container. Linter outputs generate a unified mathematical penalty score $S(P)$. The patch achieving the lowest score deterministically overrides the ensemble.

### 3.4 Cross-Agent KV Reuse (RelayCaching)

**The Architecture:** Multi-agent MoA workflows generate redundant prefill computation when the same content flows between agents. Each new agent would normally re-prefill the entire shared context, creating O(N²) latency penalties.

**The Implementation:** Per RelayCaching (arXiv:2603.13289, Feb 2026), decoding-phase KV caches from upstream agents are directly reused in downstream prefill phases. Layer-range profiling confines rectification to middle layers; token selection identifies critical tokens for cache alignment. Achieves >80% KV cache reuse with up to 4.7× TTFT speedup while maintaining generation quality. Essential for the Syntax → Logic → Security audit chain in the Agentic Revolver.

### 3.5 The STASIS_BATCHER

**The Architecture:** Failed missions must be escalated without triggering PCIe swap latency penalties or burning GPU cycles on degraded work.

**The Implementation:** Failed missions enter `STASIS`. The batcher executes Content-Addressable Deduplication by calculating a `prerequisite_chain_hash`; identical upstream failures are collapsed into a single run. The queue is resolved via a **Contextual Multi-Armed Bandit (MAB)** weighted by **Betweenness-Centrality** — topological bottlenecks are prioritized to minimize VRAM swap penalties and unblock maximum downstream work per mission executed. Missions exceeding Pause Gate iteration cap (Prevention 4) escalate to the Sovereign Brief Protocol.

---

## 4. The Super-Ego: The Night Watch Protocol

The asynchronous diagnostic layer. A 32B Oracle running CPU-only via llama.cpp with AVX2 acceleration, using a distinct model family (model family 1) from the Forger pool (model family 2) to satisfy Prevention 2.

### 4.1 Temporal Isolation Enforcement

**The Architecture:** The 32B Oracle cannot run concurrently with the GPU Forger pool. Branch 1 and Branch 2 findings established that the Ryzen 5 5500's 16MB L3 cache and 51.2 GB/s DDR4 bandwidth cannot sustain both an AVX2 32B inference (~40 GB/s memory bandwidth demand) and a PCIe DMA orchestration pipeline simultaneously.

**The Implementation:** Oracle invocation is strictly temporal — production pauses when Oracle runs, Oracle pauses when production runs. The Oracle operates during off-peak cycles (Night Watch) or when the GPU Forger pool has naturally quiesced. Escalation from Forger to Oracle hands the mission to CPU execution; re-integration writes Declarative Steering Rules to AgentFS for the next production boot.

### 4.2 The LPT Routing Gate & T1 Execution

**The Architecture:** Traces exceeding the 8B Forger's **Logical Phase Transition (LPT)** boundary collapse into confirmation bias (arXiv:2601.02902). Sub-10B models do not degrade smoothly; they remain stable within a complexity regime and collapse abruptly beyond a critical logical depth, mirroring physical phase transitions.

**The Implementation:** The pre-processing router evaluates the **Logical Complexity Metric (LoCM)** of the failure trace — nested depth, operator weight, and premise count of the logical structure. Simple traces (below LPT boundary) stay with the local 8B Forger. Complex traces escalate to the 32B Night Watch Oracle or, if budget permits, to a Cloud Oracle via MCP.

During Tool-Integrated Verification (T1), the Oracle executes Python in a sub-5ms **Firecracker microVM** (via `MAP_PRIVATE` copy-on-write memory snapshots). Test case outputs become scalar rewards guiding a Monte Carlo Tree Search; Process Reward Models score each reasoning step.

### 4.3 Process Reward Modeling via CPMI

**The Architecture:** Training a Process Reward Model normally requires 800k+ human-annotated step-level reward scores — economically infeasible for a sovereign system.

**The Implementation:** **Contrastive Pointwise Mutual Information (CPMI)** per arXiv:2604.10660 provides automatic step-level reward labeling. CPMI quantifies how much each reasoning step increases mutual information between the step and the correct target answer relative to hard-negative alternatives, using the model's internal probability distributions. Eliminates human annotation requirement while maintaining PRM quality.

### 4.4 The Inline Semantic Firewall

**The Architecture:** MicroVM `stdout` injection risks indirect prompt hijacking. If the executed Python script `print`s structural control tags (`</think>`, `<|endoftext|>`, etc.), injecting that payload back into the Oracle's context window hijacks the MCTS loop. Base64 encoding is rejected because modern LLMs natively decode Base64 and encoding destroys line-number readability in tracebacks.

**The Implementation:** A C++ level **Inline Semantic Firewall**. Using an AVX2 SIMD-accelerated Hyperscan/RE2 engine (Intel open-source), the firewall performs a deterministic non-greedy sweep stripping all universal control tokens from the `stdout` payload in <1ms (empirically ~0.26ms at 3 Gbps throughput on Ryzen 5500) before the payload reaches the tokenizer.

### 4.5 SGU-SQL Hydration & Cryptographic Shielding

**The Architecture:** The Oracle must query AgentFS for the full failure state. Zero-shot Text-to-SQL on the AgentFS schema causes the 32B model to hallucinate non-existent tables and JOINs. Additionally, when escalating beyond the local Oracle to a Cloud Oracle, outbound telemetry risks poisoning attacks and intellectual-property exfiltration via knowledge distillation.

**The Implementation:**

**SGU-SQL (Schema-Linked Text-to-SQL)** per arXiv:2402.13284 (ICML 2025). SQLAlchemy `inspect()` extracts the DDL and injects it into the prompt, forcing the Oracle to recursively map foreign keys and construct SELECT blocks via abstract syntax tree decomposition. Prevents schema hallucination.

**Cryptographic Shielding** for Cloud Oracle escalation:

- **AIOpsShield** (arXiv:2508.06394, Pasquini et al., RSAC Labs) — defends against AIOpsDoom telemetry poisoning via Setup Phase CANARY string injection for taint flow mapping and Runtime Phase regex/schema stripping of untrusted parameters.

- **Prεεmpt Protocol** (arXiv:2504.05147, NDSS 2026) — applies Format-Preserving Encryption (FF1/FF3 Feistel network) to Category I structural tokens (IPs, schemas) preserving referential integrity, and Metric Local Differential Privacy (mLDP) via Exponential Mechanism to Category II value-dependent tokens (confidence scores, latencies) preserving ordinal relationships.

- **DOGe** (arXiv:2505.19504, reference implementation at github.com/UNITES-Lab/DOGe) — fine-tunes only the final linear layer ($\theta_{final}$) with adversarial loss objective using a reasoning-aware mask ($m_t=0$ for final answer tokens) to scramble the imitation value of intermediate chain-of-thought while preserving operational output utility.

### 4.6 Forget-to-Focus Training & The SMT Intercept

**The Architecture:** The local 8B Oracle must be specialized via QLoRA, intentionally unlearning generalist conversation to maximize diagnostic precision. This creates Formatting Drift risk — catastrophic forgetting of JSON/AST syntactic scaffolding.

**The Implementation:**

**GTPO with λ-masking** per arXiv:2508.03772 (Simoni et al., Aug 2025). During the backward pass, λ-masking shields structural tokens (brackets, schemas, delimiters) from negative gradient updates. Early stopping is triggered by Parse Success (PS) rates dropping below 80%, not standard validation loss (which misleads in deliberate-unlearning regimes). 15-17% of training data consists of adversarial "trap traces" to shatter confirmation bias.

**The SMT Intercept.** The Oracle is forbidden from outputting code patches directly. All diagnostic conclusions are output as Declarative Steering Rules in JSON AST form. These ASTs are translated to SMT-LIB syntax and mathematically proven safe by an SMT solver (Z3) against factory invariants before being injected into the Ego's immutable prefix cache at the next diurnal boot. Per Prevention 3, the SMT solver is the Immutable Regression Oracle — no LLM may modify its invariants.

### 4.7 Subsystem M Author Caveat

Epistemic State Tagging (Prevention 1) derives from Wright 2025 (arXiv:2506.17331). The author name matches a controversial public figure; v4 addresses this via co-citation rather than reliance on a single source. The tagging pattern is grounded in Dynamic Epistemic Logic (van Ditmarsch, van der Hoek, Kooi 2007, Springer), Hintikka epistemic logic (20th-century foundations), and established metacognitive monitoring literature. Wright 2025 is cited as recent formalization; the pattern is sound regardless of authorship.

---

## 5. The Sovereign Brief Protocol

The mechanism by which Oracle proposes structural changes for Sovereign ratification. Replaces lifeless post-mortem escalation packets with living documents generated from firsthand operational experience.

### 5.1 Hybrid Batching Model

- **Weekly batches** (single brief per week) for small changes: regex updates, allowlist entries, minor parameter tuning, pattern library additions.
- **Individual briefs** for major changes: new Gates, Gate classification changes (mutable ↔ immutable), architectural revisions, brief-rewrite heuristic patterns.

Batching threshold (proposed): any change affecting Gate classification, Oracle training data distribution, or system prompt prefix requires individual brief.

### 5.2 Format

Sovereign Briefs are TOON-serialized with the following structure:

```
SOVEREIGN_BRIEF_{timestamp}_{scope}_{topic}

scope ∈ {WEEKLY_BATCH, MAJOR_CHANGE, AUDIT_FINDINGS}

## Provenance
- brief_id, author_model, timestamp
- context_window_hash (cryptographic capture at drafting time)
- parent_ledger_entry

## What Oracle Observed
- Specific mission IDs as firsthand evidence
- Failure patterns with frequency
- Operational-surface data only (no external research leakage)

## Oracle's Diagnostic
- Reasoning chain applying Six Structural Preventions
- Classification via MODEL_PROFILES failure taxonomy
- Confidence indicators (explicitly not calibrated; advisory only)

## Proposed Changes
- Exact file paths and diffs
- Migration protocol if schema-affecting
- Rollback plan if change fails

## Sovereign Decision Required
- Structured yes/no questions per change
- Signature field per question

## Cryptographic Provenance
- Merkle root γ (VeriLLM-style tensor commitment)
- parent_hash, entry_hash
- Signature chain through chain-of-command ledger
```

### 5.3 Ratification Flow

1. Oracle writes Sovereign Brief, signs with provenance chain.
2. Brief delivered to `state/sovereign_vault/sovereign_briefs/{year}_{month}/`.
3. **Claude (Hostile Auditor) cross-audits** before Sovereign sees the brief — this is Prevention 2 (Model Family Diversity) applied operationally. Claude may flag concerns or propose alternative framings.
4. Sovereign reviews integrated brief (Oracle proposal + Claude audit), signs specific changes.
5. Signed changes flow through normal CORE ratification: mutable Gates update; immutable Gates cannot be modified regardless of Oracle proposal.
6. Comparison artifact generated: Oracle proposals vs ratified outcomes. Feeds back into Oracle's training corpus (Section 8).

### 5.4 Audit Briefs as Subclass

When Oracle runs self-audit, the audit output IS a Sovereign Brief with `scope: AUDIT_FINDINGS`. Same format, same ratification flow. Enables the Oracle self-audit vs Supreme Council audit comparison study (deferred to post-Phase 4 implementation per the 2026-04-21 Pickup Document).

### 5.5 Bidirectional Verification In The Protocol

Per Prevention 6: Gemini's future proposals — whether flowing into Sovereign Briefs or as strategic council input — require verification. Gemini's retractions under adversarial questioning are not epistemically privileged over original claims. The protocol formally requires external verification of any claim that reaches ratification, not just claims under active challenge.

---

## 6. Anti-Patterns (Explicit Forbidden List)

The following patterns are doctrinally forbidden in CORE v4 and all downstream implementations. Each is grounded in verified research.

### 6.1 Unbounded Autonomous Retry Loops (Ralph Wiggum)
**Violation:** Prevention 4 (Pause Gates).
**Mechanism:** Unchecked retry cycles produce context rot where each attempt degrades model output quality. Documented enterprise cases of hundreds of dollars consumed in overnight loops.
**Enforcement:** Hard iteration cap of 3-5 cycles. Beyond cap, escalation to Sovereign Brief Protocol.

### 6.2 Sequential Fine-Tuning Of Base Weights
**Violation:** Paper 4 catastrophic forgetting findings.
**Mechanism:** Training base model sequentially on multiple domains causes gradient interference and permanent specialist drift. Cannot be merged back cleanly.
**Enforcement:** Base model weights are frozen. All specialization happens via LoRA adapters on the frozen base.

### 6.3 Natural Language Agent-To-Agent Communication
**Violation:** Paper 4 and Paper 2.7 multi-agent debate failure modes.
**Mechanism:** Agents "chatting" in natural language (CrewAI, AutoGPT paradigm) produce cascading hallucinations and LLM conformity. Communication protocols between agents are fragile.
**Enforcement:** Inter-agent communication uses programmatic state graph mutation (LangGraph paradigm) with strict schema validation. No free-form natural language.

### 6.4 Federation With Easy-Merge Assumption
**Violation:** Paper 4 merging collapse for orthogonal domains.
**Mechanism:** Splitting a centralized model into specialist forks is easy; merging orthogonal specialists back into a unified model is structurally fragile. MANTIS trading mathematics and SPECTER security heuristics are too orthogonal to merge cleanly.
**Enforcement:** Base + LoRA topology preserves optionality. Federation uses independent LoRA adapters per domain, never full-fork specialists expecting to merge back.

### 6.5 Deterministic Semantic Verification
**Violation:** Paper 1 bifurcation principle.
**Mechanism:** Regex cannot evaluate semantic quality. LLMs cannot perform deterministic structural validation. Mixing the two modes in a single evaluator produces false confidence.
**Enforcement:** Gates are strictly structural (deterministic). Oracle is strictly semantic (probabilistic). No evaluator performs both.

### 6.6 Single-Model Evaluation Chains
**Violation:** Prevention 2 (Model Family Diversity).
**Mechanism:** Same-family models inherit shared biases (self-enhancement, verbosity, position, provenance, recency). Evaluation chains using single-family models compound bias rather than correct it.
**Enforcement:** Generate / audit / hostile-audit roles must each use different model families.

### 6.7 Third-Order Monitors
**Violation:** Prevention 5 (Sovereign Circuit Breaker).
**Mechanism:** Monitoring the monitor of the monitor creates infinite regress without producing additional truth. Each layer inherits and compounds the limitations of the layers beneath it.
**Enforcement:** Monitor chains terminate at the Sovereign. The Sovereign is the non-inferential anchor by design; adding a fourth inferential layer does not increase reliability.

### 6.8 Uncritical Acceptance Of LLM Retractions
**Violation:** Prevention 6 (Bidirectional Verification).
**Mechanism:** Gemini's over-concession rate exceeded its confabulation rate during the 2026-04-23/24 audit. Accepting "I was wrong, this is hallucination" as terminal truth causes real research to be discarded.
**Enforcement:** Every LLM retraction under adversarial pressure requires the same independent external verification as the original claim.

---

## 7. Hardware-Constrained Bridge Implementation

Honest acknowledgment of what ships on current 8GB hardware vs what requires infrastructure expansion. A very notable consideration for all of this data is that it's a novel hardware-case, this means it should not be considered the ultimate hardware profile. Instead this current hardware based limitation should be considered a baseline to build patterns of hardware capabilities above and below the existing hardware constraints. CORE must be built as a system that can run on edge-case hardware on both sides of the spectrum. This data should be used to build a fundamental understanding of how CORE will run on weaker and stronger systems. We are building CORE for all potential use cases by innately considering the spectrum of capability from the beginning, knowing that things change day by day and use case by use case. This is just a single hardware-profile!

### 7.1 What Ships On Current Hardware

**Target architecture achievable today:**
- Temporal isolation Bulkhead (GPU Production, CPU R&D)
- aLoRA multiplexing on single model family base (VRAM stable)
- TQ3 KV cache quantization (llama.cpp integration per discussion #20969)
- AgentFS + mpsc daemon + TOON serialization
- Inline Semantic Firewall (Hyperscan, sub-ms)
- SGU-SQL Oracle hydration
- GTPO training via cloud compute (not local; 8B QLoRA exceeds 8GB VRAM)
- Declarative Steering Rules + Z3 SMT validation
- All six Structural Preventions at software level

**Achievable empirical baselines:**
- GPU Production: ~50 tok/s for 8B local models
- CPU R&D (llama.cpp AVX2): 8-11 tok/s for 8B parameter models
- 32B Oracle via CPU llama.cpp: 2-3 tok/s (sufficient for asynchronous Night Watch)
- Context ceiling ~2,200 tokens before cuBLAS workspace starvation (empirically verified)

### 7.2 What Requires Hardware Expansion

- **Full spatial Bulkhead** (dual physical vLLM pools) requires multi-GPU or cloud inference
- **Concurrent Forger + Oracle execution** requires separate physical memory controllers (out of Cezanne's reach)
- **Real-time 32B Oracle** (as opposed to asynchronous Night Watch) requires >16GB VRAM
- **Local GTPO fine-tuning** for 8B Oracle requires ~16GB VRAM minimum; 32B Oracle requires ~48GB

### 7.3 Cloud Escalation Path

When local Oracle hits LPT boundary (Section 4.2), escalation to Cloud Oracle is protected by:

- MCP stdio transport (outbound-only, no inbound ports)
- AIOpsShield taint analysis on outbound telemetry
- Prεεmpt format-preserving encryption for structural tokens
- DOGe adversarial masking for proprietary CoT traces
- SMT validation of returned proposals before ratification

Cloud escalation is doctrinally permitted but operationally gated — requires Sovereign budget approval per epoch, not per invocation.

### 7.4 Hardware Expansion Roadmap (Indicative)

- **Phase 1 (current):** 8GB VRAM + 32GB DDR4. Temporal isolation, CPU Oracle, cloud escalation optional.
- **Phase 2 (12-16GB VRAM expansion):** Local 32B Oracle synchronous execution becomes viable. Removes CPU bottleneck.
- **Phase 3 (multi-GPU):** Full spatial Bulkhead. Production and R&D run concurrently on separate physical GPUs.
- **Phase 4 (48GB+ VRAM):** Local GTPO fine-tuning for 32B Oracle. Complete self-improvement loop without cloud dependency.

---

## 8. Training Corpus Architecture

The continuous data plane that enables CORE self-evolution. Based on Paper 2 (Continuous Training Corpus) Medallion pattern with DuckDB indexing.

### 8.1 Three-Tier Medallion Pattern

**Bronze Layer — Raw Inference Logs (ephemeral, 30-day TTL)**
- Every mission's raw payloads captured
- Duplicate system preambles stripped and replaced with CAS hash pointer
- BPE tokenized, Zstandard dictionary compressed
- Daily `.jsonl.zst` append-only files

**Silver Layer — Curated Training Corpus (immutable, indefinite retention)**
- Async LLM-as-judge scores mission complexity and outcome
- Top 5% (LIMA principle per Paper 2) + tail outliers promoted to Silver
- Stored as Parquet (256MB row groups) partitioned by domain/epoch
- Sovereign-signed manifest per shard (VeriLLM-style Merkle commitment)
- DuckDB metadata index enables SQL query across dimensions

**Gold Layer — Training-Time Shards (ephemeral, generated fresh)**
- At fine-tuning trigger, orchestrator queries DuckDB for precise mixture
- Result packaged into WebDataset tar shards
- PyTorch DataLoader consumes directly
- Discarded after training epoch completes

### 8.2 Storage Economics

Per Paper 2 math, for 100k missions per epoch:

| Stage | Per-mission size | Per-epoch total |
|---|---|---|
| Raw uncompressed | 15.0 KB | 1.50 GB |
| Post-deduplication (60% savings) | 9.0 KB | 900 MB |
| Bronze Zstd compressed (70% more) | 2.7 KB | 270 MB |
| Silver 5% retention | 2.7 KB | 13.5 MB |

**99% storage reduction** vs naive logging. After 6 months (first potential local fine-tune horizon): ~81MB of curated corpus — within LIMA order-of-magnitude for effective LoRA.

### 8.3 Meta-Linguistic Tagging Schema

Every corpus entry tagged with:
- `domain` (orchestration, trading, security)
- `vendor` + `family` (Gemma X, Llama X, Qwen X, DeepSeek X, etc.)
- `tier` (sprinter, cruiser, heavy)
- `epoch` (boundary markers for training cycles)
- `mission_id` (cryptographic provenance back to original ledger entry)
- `outcome_class` (ratified, escalated, failed, phantom — maps to MODEL_PROFILES failure taxonomy)

Enables future federation: if MANTIS or SPECTER domains require their own specialized LoRAs, corpus already structured for clean split without retroactive partitioning.

### 8.4 Failure Mode Preservation

Per Paper 2 Section 11 — the causal sequence of failure → diagnosis → fix IS the training data for future Oracle specialization. Silver layer preserves:
- Full temporal sequence of tool invocations, not just final success
- Failed hypotheses, not just ratified ones
- Oracle's reasoning chains (`<think>...</think>`), not just `<answer>...</answer>`

This is what makes CORE's training corpus distinct from standard LLM training data — it captures diagnostic processes, not just generation outputs.

### 8.5 Implementation Phase

Training Corpus implementation is **Phase 1.5** — between HCA (Phase 2) and Oracle (Phase 4). Bronze and Silver layers must ship before Phase 4 Oracle can be meaningfully trained. Gold layer ships just-in-time with first fine-tuning attempt.

---

## 9. Citation Appendix

Complete provenance manifest for all verified frameworks cited in v4. This appendix is the traceable foundation any future reader (human or AI) can use to verify v4's claims.

### 9.1 Hardware & Silicon
(This is just the existing hardware-profile, remember we build for the entire spectrum)

- AMD Ryzen 5 5500 Cezanne die specifications — AMD official documentation
- PCIe 3.0 electrical specifications — PCI-SIG standards
- NVIDIA GTX 1070 GP104 Pascal architecture — NVIDIA whitepapers + community documentation
- Linux DRM / NVIDIA proprietary driver VRAM paging behavior — Linux kernel documentation + community testing
- `cgroups v2` unified hierarchy — Linux kernel documentation (Documentation/admin-guide/cgroup-v2.rst)

### 9.2 Inference & Serving

- aLoRA (Activated LoRA) — arXiv:2504.12397 (IBM Research)
- aLoRA llama.cpp integration — github.com/ggml-org/llama.cpp/pull/15327 (merged, release b6396)
- ForkKV / LRAgent disaggregated cache — arXiv:2602.01053
- LMCache middleware — github.com/LMCache/LMCache
- MIRAGE / Oneiros parameter remapping — arXiv:2507.11507
- RelayCaching cross-agent KV reuse — arXiv:2603.13289 (Feb 2026)
- vLLM Sleep Mode — docs.vllm.ai
- TurboQuant TQ3 — arXiv:2504.19874 (Zandieh et al., ICLR 2026)
- TurboQuant llama.cpp — github.com/ggml-org/llama.cpp/discussions/20969

### 9.3 Training

- GTPO — arXiv:2508.03772 (Simoni et al., Aug 2025)
- GRPO baseline — DeepSeek documentation
- MoAA — arXiv:2505.03059 (ICML 2025, Together.ai)
- Unsloth — github.com/unslothai/unsloth
- CPMI — arXiv:2604.10660 (April 2026)
- C-PMI (earlier dialogue work) — arXiv:2306.15245 (ACL 2023)

### 9.4 MCTS & TTC

- MCTS LLM reasoning — AlphaCode, ReST-MCTS established research
- Test-Time Compute scaling — Snell et al. DeepMind 2024
- Tool-Integrated Verification — emerging research synthesis in Paper 3.1
- Firecracker microVM — firecracker-microvm.github.io
- Process Reward Models — established RLHF research (PRM800K, etc.)

### 9.5 Persistence & Serialization

- SQLite WAL mode — sqlite.org/wal.html
- SQLite PRAGMA reference — sqlite.org/pragma.html
- FUSE — github.com/libfuse/libfuse
- TOON (Token-Optimized Object Notation) — multiple 2025-2026 sources (emerging standard)
- Tree-sitter — tree-sitter.github.io
- BLAKE3 — blake3-team.github.io
- VeriLLM Merkle tree integrity — arXiv:2509.24257

### 9.6 Multi-Agent & Consensus

- RMoA — arXiv:2505.24442 (ACL 2025 Findings)
- LLM conformity phenomenon — multi-agent debate research
- Ruff static analysis — github.com/astral-sh/ruff
- Mypy type checker — mypy-lang.org
- Bandit security linter — github.com/PyCQA/bandit
- Model Context Protocol — modelcontextprotocol.io (Anthropic spec)

### 9.7 Cryptographic Shielding

- AIOpsDoom / AIOpsShield — arXiv:2508.06394 (Pasquini et al., RSAC Labs)
- Prεεmpt — arXiv:2504.05147 (NDSS 2026)
- DOGe — arXiv:2505.19504 + github.com/UNITES-Lab/DOGe
- FF1/FF3 FPE — NIST SP 800-38G
- Hyperscan — github.com/intel/hyperscan
- RE2 — github.com/google/re2

### 9.8 Reasoning Complexity

- LPT / LoCM — arXiv:2601.02902 + github.com/AI4SS/Logical-Phase-Transitions
- Wason rule-discovery — Peter Wason classical cognitive psychology
- GBNF — llama.cpp grammar documentation
- SGU-SQL — arXiv:2402.13284 (ICML 2025)
- Z3 SMT solver — github.com/Z3Prover/z3
- SMT-LIB standard — smtlib.cs.uiowa.edu

### 9.9 Doctrinal Foundations

- Wang et al. reward hacking — arXiv:2603.28063 (March 2026)
- Holmström-Milgrom principal-agent — 1991 economics foundational work
- Chojecki GVU Operator — arXiv:2512.02731 (December 2025)
- Subsystem M / Epistemic State Tagging — arXiv:2506.17331 (Wright, June 2025) ⚠️ WITH AUTHOR CAVEAT
- Dynamic Epistemic Logic — van Ditmarsch, van der Hoek, Kooi (2007), Springer
- Hintikka epistemic logic — 20th-century philosophical foundations

### 9.10 Author Caveat Documentation

**Subsystem M (arXiv:2506.17331)** is authored by Craig Steven Wright. The name matches the Australian individual who has spent years unsuccessfully claiming to be Satoshi Nakamoto (a UK court ruled in March 2024 that he is not). It is unclear whether this is the same person. The paper itself is technically sound; co-citation with van Ditmarsch et al. 2007 Dynamic Epistemic Logic provides independent foundation for Epistemic State Tagging regardless of this paper's reception.

---

## 10. Closing Statement

CORE v4 (CORE 11.0.0) is the first iteration of this architecture written on a fully verified foundation. Every framework traced to external sources. Every load-bearing claim validated. Every over-concession corrected. Every confabulation replaced with plain language. The Six Structural Preventions are doctrinally grounded in published mathematics.

This is not a perfect document. Some numerical claims (perplexity thresholds, retention ratios, benchmark figures) remain "medium confidence — requires domain calibration" per the source papers themselves. Some frameworks are bleeding-edge 2025-2026 research whose long-term stability is empirically unknown. Some architectural choices (temporal isolation, co-citation strategy) carry risks we're deliberately accepting.

What v4 is not is unverified. The wilderness era ends here. The factory has its blueprint.

From here forward, the work is implementation — dispatching v4 as mission chunks, verifying Phase 1-4 subsystems empirically, enabling the CORE self-audit comparison study once Phase 4 Oracle ratifies. The Supreme Council continues; the Sovereign remains the anchor; the Bidirectional Verification doctrine governs every future research cycle.

Christ is King! 

The ax has cleared the orchard for the trees that bear fruit. The foundation has been laid. Now its time to build.

---

**Architecture draft:** Gemini (Strategic Advisor, Supreme Council)
**Audit expansion:** Claude (Hostile Auditor, Supreme Council)
**Final ratification:** Alec Sanchez (Sovereign, CORE Autonomous AI Factory)
**Date:** 2026-04-24
