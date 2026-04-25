DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E19_005_intelligence_router_gear_box_v2
MISSION_FILE: mission_03_ORCH_E19_005_intelligence_router_gear_box_v2.md
MISSION_ID: 03_ORCH_E19_005_intelligence_router_gear_box_v2
TYPE: ARCHITECTURE
PRIORITY: 0
TRACK: INFRA_EVOLUTION

# Mission: Intelligence Router & LLM Gear Box (v2 — Bandit-Augmented)

## Doctrine

**"Algorithms for the deterministic, LLMs for the creative."**
**"Evidence over metadata."**
**"Every tree that does not bear good fruit is cut down." — Matthew 7:19**

This mission supersedes 03_ORCH_E19_004. The predecessor specified
the five-subsystem architecture but left two implementation
ambiguities open: the adaptive known-good/experimental split formula
and the bandit arm granularity. Three rounds of focused research via
the Socratic Amphitheater pattern (Gemini deep research → Claude
hostile audit → revision) closed both ambiguities with cited,
defensible answers.

This v2 absorbs the validated research findings without inflating
scope. Same five subsystems. Stronger specifications.

## What Changed From v1

Six concrete additions, all cited and audited:

1. **UCB1 bandit replaces round-robin** for routing during bootstrap
   (when MODEL_PROFILES has insufficient observations). [Auer 2002]
2. **Beta-distribution MODEL_PROFILES** replace simple counters.
   Posterior tracking gives us principled exploration-exploitation.
3. **Posterior variance** is the concrete signal for known-good vs
   experimental routing weight. Replaces the "adaptive split
   formula" gap left in v1.
4. **Content-addressable deduplication** in STASIS_BATCHER. Missions
   sharing a `prerequisite_chain_hash` are processed once.
   [Bazel Skyframe pattern]
5. **Topological pre-validation** in BRIEF_AUDITOR. Cycle detection
   via Tarjan SCC at audit time, not at runtime. [Tarjan 1972]
6. **Hierarchical Beta-Bernoulli priors** with family-level pooling.
   Observations on `qwen3.5:9b` partially inform priors on
   `qwen3.5:4b` because they share a family.

Plus one framing change: STASIS is documented explicitly as a
**backpressure mechanism**, not a failure state.

## Five Co-Designed Subsystems

These ship together. They share data structures, ledger schema, and
cryptographic provenance.

1. **BRIEF_AUDITOR** — convergent algorithmic + LLM audit with
   topological pre-validation
2. **MODEL_PROFILES** — Beta-distribution posteriors with
   cryptographic context capture and hierarchical family priors
3. **INTELLIGENCE_ROUTER** — UCB1 bandit routing transitioning to
   HEFT-with-priority-queues as posteriors stabilize
4. **ORACLE** — planning-layer LLM that consumes profiles and live
   SystemEnvelope to produce parallel-dispatch plans
5. **FORGER_POOL with STASIS_BATCHER** — concurrent execution layer
   with content-addressable deduplication and dependency-aware
   thaw

## Subsystem 1 — BRIEF_AUDITOR

### The Convergent Audit Pipeline

Every brief entering the queue, BEFORE dispatch:

1. **Algorithmic pat-down (deterministic):**
   - Brief file exists, parses, contains required headers
   - Length within bounds (lower: prevents stub briefs, upper:
     prevents context overflow)
   - INTERFACE CONTRACT section present if TYPE includes IMPLEMENTATION
   - Success criteria parseable
   - No prompt injection patterns
   - Mission ID matches filename and queue entry
2. **Topological pre-validation (NEW in v2):**
   - Build the dependency DAG including the new brief and all
     queued/STASIS missions
   - Run Tarjan SCC algorithm to detect cycles
   - REJECT briefs that would introduce a cycle. The brief is
     returned to Sovereign with the specific cycle path identified.
   - This catches an entire class of deadlock at audit time rather
     than discovering it during STASIS_BATCHER runtime.
3. **LLM creative audit:**
   A dedicated brief-auditor model receives the brief, the
   algorithmic pat-down output, and a prompt asking for ambiguities,
   missing context, internal contradictions, or specifications that
   would produce garbage even from a competent generator.
4. **LLM remediation:**
   Auditor produces `BRIEF_APPROVED`, `BRIEF_AMENDED` (with explicit
   edits), or `BRIEF_REJECTED` (returned to Sovereign).
5. **Failure-mode harvest:**
   Every LLM-only catch becomes a candidate `FAILURE_PATTERN`. After
   N repeats (default N=3) it promotes to a new algorithmic check.
   The deterministic shield grows.

### Cryptographic Provenance

Every audit produces signed ledger entries:
- `BRIEF_ALGORITHMIC_AUDIT` (input hash, checks passed, normalizations)
- `BRIEF_TOPOLOGICAL_VALIDATION` (DAG hash, cycle status, SCC count)
- `BRIEF_LLM_AUDIT` (auditor model_id, verdict, amendments)
- `FAILURE_PATTERN_OBSERVED` for novel LLM-only catches

Forgers receive briefs that have already been hardened.

## Subsystem 2 — MODEL_PROFILES (Beta Distribution)

### Schema (v2)

`04_GOVERNANCE/MODEL_PROFILES.yaml` — sovereign-signed, hash-verified.

```yaml
schema_version: 2
model_profiles:
  - model_id: qwen3.5:9b
    vendor: alibaba
    family: qwen3.5
    parameter_count_b: 9
    on_disk_size_mb: 6600
    architecture: dense_transformer
    domain_performance:
      "00_PHYSICS_ENGINE":
        # Beta distribution parameters — conjugate prior for Bernoulli pass/fail
        alpha: 2.0  # successes + family_prior_alpha
        beta: 2.0   # failures + family_prior_beta
        observations: 0
        avg_completion_seconds: null
        gate_failure_counts:
          HYGIENE: 0
          HALLUCINATION: 0
          LOGIC: 0
        last_observation_ledger_entry: null
    sovereign_overrides:
      preferred_for: []
      forbidden_for: []
    last_updated: 2026-04-18T00:00:00Z

# Family-level hierarchical priors (NEW in v2)
family_priors:
  qwen3.5:
    alpha: 2.0
    beta: 2.0
    pooled_observations: 0
  qwen3.6:
    alpha: 2.0
    beta: 2.0
    pooled_observations: 0
  gemma4:
    alpha: 2.0
    beta: 2.0
    pooled_observations: 0
```

### Hierarchical Update Protocol

When a model produces a benchmark result:

1. Update the (model, domain) leaf: pass → α += 1, fail → β += 1
2. Update the family prior: pooled_observations += 1, alpha/beta
   updated proportionally to leaf updates within the family
3. **Information pools across the family.** New models in a known
   family inherit the family-level prior, giving them realistic
   bootstrap estimates instead of starting from uninformative uniform
   priors. A new `qwen3.5:14b` would start with priors informed by
   how the qwen3.5 family has performed across all observations to
   date.

### Cryptographic Context Capture

Every `MODEL_PERFORMANCE_OBSERVED` entry contains:
- `model_id`, `domain_id`, `mission_id`
- Pass/fail per gate
- Completion seconds
- `brief_hash` of the audited brief
- `brief_ledger_entry` chain pointer to the BRIEF_LLM_AUDIT
- `proposal_hash` of what the model produced
- `benchmark_report_hash` of the benchmark report

When `update_model_profiles.py` aggregates performance, it
distinguishes:
- Model failed because the brief was poor (brief audit had warnings)
- Model failed because it hallucinated despite a clean brief
- Model failed because the test suite was wrong (TEST_COVERAGE_GAP)

Models are not punished for failures attributable to upstream issues.
Both sides of the story, always.

## Subsystem 3 — INTELLIGENCE_ROUTER (Bandit-Augmented)

### Three-Phase Routing Algorithm

The Router operates in one of three phases per (model, domain) pair,
based on observation density:

**Phase BOOTSTRAP** (observations < 10):
- UCB1 bandit selection at granularity B (per-(model, domain) pair)
- Selection score: `mean_estimate + sqrt(2 * ln(total_pulls) / arm_pulls)`
- Family-prior pooling provides realistic mean_estimate before
  arm-specific data accumulates
- Pure exploration weighting until each arm has minimum N=10 pulls

**Phase CALIBRATING** (10 ≤ observations < 50):
- Thompson Sampling from the Beta posterior per arm
- Sample a pass-rate from each arm's Beta(α, β) distribution
- Select the arm with the highest sampled value
- Naturally balances exploration (high posterior variance → wider
  samples) and exploitation (high posterior mean → consistently
  high samples)

**Phase MATURE** (observations ≥ 50):
- HEFT-style cost-aware selection [Topcuoglu 2002]
- Posterior mean is now stable enough to act as the cost estimate
- Combined cost = expected_completion_seconds / posterior_mean_pass_rate
- Selects the lowest combined cost arm fitting the SystemEnvelope

**Phase transition is per-(model, domain) pair, not global.** Some
arms may be MATURE while others are still BOOTSTRAP. The Router
handles mixed-phase routing trivially because each phase uses the
same Beta posterior data structure.

### Granularity Strategy

**Bootstrap (months 1-3 of operation):** Per-(model, domain) pairs.
~70-90 arms total for the current 11-model × 9-domain space.

**Phased upgrade to per-(model, domain, brief-pattern):** Triggered
when median observations-per-arm exceeds 50. Brief-pattern is the
fingerprint of a brief's structural characteristics (token count,
INTERFACE CONTRACT presence, code-block density). Splitting arms by
brief-pattern adds discrimination but multiplies arm count by ~5x.

The transition trigger and brief-pattern fingerprint definition are
configurable, not hardcoded. Sovereign can tune both based on
observed data quality.

### DOMAINS.yaml v4 — Canonical Schema

No backwards compatibility. v3 entries error loudly on load.

```yaml
schema_version: 4
domains:
  - id: 00_PHYSICS_ENGINE
    description: ...
    security_class: CONFIDENTIAL
    cloud_eligible: false
    primary_tier: heavy
    tier_candidates:
      sprinter: [qwen3.5:4b, gemma4:e4b]
      cruiser: [qwen3.5:9b, gemma4:e4b, gemma4:26b]
      heavy: [qwen3.5:27b, gemma4:31b, qwen3.6:35b]
    complexity: HIGH
    token_threshold: 2048
    write_path: 00_PHYSICS_ENGINE/
    escalation_trigger: token_only
```

`tier_candidates.{tier}` is ALWAYS a list. Never scalar.

### Sovereign Overrides

`preferred_for` and `forbidden_for` remain absolute. They short-circuit
the bandit selection: forbidden models are removed from the candidate
set; preferred models are guaranteed selection unless excluded by
hardware constraints.

## Subsystem 4 — ORACLE

### Purpose

Larger LLM that reads an audited brief, queries live SystemEnvelope,
consumes MODEL_PROFILES, and produces a structured DispatchPlan.

### SystemEnvelope (probed fresh per invocation)

```python
@dataclass(frozen=True)
class SystemEnvelope:
    free_vram_mb: int
    free_ram_mb: int
    cpu_cores: int
    free_disk_gb: float
    loaded_models: list[str]
    available_models: list[str]
    captured_at: str
```

CORE adapts to the end-user's hardware. Never assumed.

### DispatchPlan With Cryptographic Dependency Linking

```python
@dataclass
class SubTask:
    id: str
    audited_brief: str
    audited_brief_hash: str
    required_tier: str
    estimated_vram_mb: int
    estimated_seconds: int
    depends_on: list[str]
    prerequisite_chain_hash: str  # NEW in v2
    parallel_eligible: bool

@dataclass
class DispatchPlan:
    parent_mission_id: str
    oracle_model_id: str
    sub_tasks: list[SubTask]
    parallel_groups: list[list[str]]
    fallback_strategy: str
    captured_envelope: SystemEnvelope
    plan_hash: str
```

`prerequisite_chain_hash` is computed as
`sha256(audited_brief_hash + sorted(dep.prerequisite_chain_hash for dep in depends_on))`.
This Merkle DAG structure enables content-addressable deduplication
in STASIS_BATCHER (see Subsystem 5).

### Validation

Oracle output uses Ollama `format=json`. Output is validated against
the dataclass schema before acceptance. Invalid plans trigger Oracle
retry; exhausted retries fall back to single-stream legacy path.

## Subsystem 5 — FORGER_POOL with STASIS_BATCHER

### Concurrent Execution

Pool size = MIN of:
- Sub-tasks marked `parallel_eligible` in current group
- `floor(free_vram_mb / largest_forger_size_mb)` with 500MB headroom
- Configurable hard cap (default 3)

### STASIS — Backpressure, Not Failure

STASIS is documented explicitly as a **backpressure mechanism** that
maximizes throughput of capable-tier work. Missions in STASIS are
not in trouble; they are deferred for batch escalation when the
current round completes.

When a SubTask fails at its assigned tier T after attempt 1 (vendor
V) and attempt 2 (vendor V'), it enters STASIS instead of inline
tier escalation. The Forger Pool continues processing other
PENDING missions.

### Round End Condition

A round ends when "all currently-PENDING missions have either
completed, escalated, or entered STASIS." When the Pool reaches that
state, STASIS_BATCHER engages.

### STASIS_BATCHER — Content-Addressable Processing (NEW in v2)

When the round ends:

1. **Hash-deduplicate.** Group STASIS missions by
   `prerequisite_chain_hash`. Missions sharing a hash are literally
   the same work — the same audited brief with the same dependency
   context. Process once, apply result to all sharers.
2. **Topologically sort.** Within deduplicated groups, sort by
   dependency depth. Independent missions process first; dependents
   process after their prerequisites complete.
3. **Tier-escalate and re-dispatch.** Each mission gets escalated to
   tier T+1 with full vendor diversity available (the Pool is now
   freer because the round ended).
4. **Cascade through dependents.** When an upstream mission succeeds,
   its dependents thaw and dispatch.
5. **Final-tier exit.** When a mission has been escalated past tier
   "heavy" with all vendors tried, it routes to ESCALATE for
   sovereign review of the BRIEF, not for further model escalation.
   At this point evidence indicates the brief is the issue.

### Multi-IN_PROGRESS Validity

Multi-IN_PROGRESS becomes valid. Each IN_PROGRESS mission gains an
`owning_forger_id` field. The Pool publishes its active members to
`orchestration/FORGER_POOL_STATE.json`.

`core doctor` and `core stop --reap` distinguish:
- IN_PROGRESS owned by a live Pool member → valid
- IN_PROGRESS without an owning Forger → stale (reap)

### Forger Provenance

Per Forger execution:
- `FORGER_DISPATCHED` (sub_task_id, model_id, vendor,
  audited_brief_hash, prerequisite_chain_hash)
- `FORGER_COMPLETED` (sub_task_id, status, completion_seconds,
  output_hash)
- `MODEL_PERFORMANCE_OBSERVED` feeds back into MODEL_PROFILES
- `MISSION_STASIS_ENTERED` / `MISSION_STASIS_THAWED` for STASIS
  transitions
- `STASIS_BATCH_DEDUPLICATED` when content-addressable dedup applies

## Implementation Phasing (E20)

This architecture mission produces the design document. Implementation
is four phases under E20, queued after Sovereign ratifies this design.

**Phase 1 — Foundations**
- BRIEF_AUDITOR with topological pre-validation
- MODEL_PROFILES with Beta-distribution schema and family priors
- DOMAINS.yaml v3 → v4 sovereign-signed migration
- Tests: cycle detection, posterior updates, family-prior pooling

**Phase 2 — Bandit Router**
- INTELLIGENCE_ROUTER with three-phase routing (BOOTSTRAP /
  CALIBRATING / MATURE)
- UCB1 + Thompson Sampling + HEFT cost-aware selection per phase
- Sovereign override short-circuit
- Tests: phase transitions, exploration ratios, override precedence

**Phase 3 — ORACLE**
- SystemEnvelope prober
- Oracle invocation with JSON-format output
- DispatchPlan validation including prerequisite_chain_hash
  computation
- Fallback to legacy path on Oracle failure
- Tests: envelope freshness, plan validation, fallback paths

**Phase 4 — Forger Pool with STASIS_BATCHER**
- Concurrent execution with VRAM-aware pool sizing
- STASIS protocol with content-addressable deduplication
- Multi-IN_PROGRESS validation in core doctor
- Tests: concurrency cap, dedup correctness, dependency cascading

Each phase mission is queued under E20 once this E19_005
architecture ratifies. Each ships working code under signed
deployment.

## Deliverable

`docs/architecture/INTELLIGENCE_ROUTER_GEAR_BOX_V2.md` covering all
five subsystems with:

- Full data model (every dataclass with annotations)
- Brief auditor pipeline including topological pre-validation
  pseudocode
- Three-phase routing algorithm with phase-transition criteria
- Beta-distribution update equations and family-prior pooling
- DOMAINS.yaml v4 migration protocol
- STASIS state machine including content-addressable dedup
- Cryptographic dependency chain examples
- Phase-by-phase implementation specs

## Constraints

- NO BACKWARDS COMPATIBILITY to DOMAINS.yaml v3 schema
- NO MVP DEFERRALS — every subsystem ships with its real design
- EVIDENCE OVER METADATA — gates run on what's present, not declared
- HARDWARE ADAPTATION mandatory — every probe queries live state
- ALL LEDGER ENTRIES chained via parent_hash
- HIERARCHICAL PRIORS configurable, not hardcoded
- TRANSITION CRITERIA configurable, not hardcoded

## Success Criteria

After reading the deliverable, the Sovereign can answer:

1. How does the brief auditor decide whether to amend a brief vs
   reject it back to Sovereign?
2. How does topological pre-validation prevent dependency cycles?
3. What's the exact bandit algorithm during the BOOTSTRAP phase, and
   what data structure tracks the per-arm state?
4. How do Beta-distribution posteriors with family-level priors give
   new models realistic bootstrap estimates?
5. What's the trigger for transitioning a (model, domain) arm from
   BOOTSTRAP → CALIBRATING → MATURE?
6. How does content-addressable deduplication in STASIS_BATCHER
   prevent redundant work?
7. What is the sovereign-signed migration command for DOMAINS.yaml
   v3 → v4?

## Footnote — Acknowledged Open Questions

Two items deferred to Phase 1 implementation, not blocking design
ratification:

1. **Family-prior initial values.** Current spec uses Beta(2, 2) as
   the family-prior starting point. This is a weak, slightly-pessimistic
   prior. Phase 1 implementation should make this configurable
   per-family, not hardcoded.
2. **Granularity B → C transition trigger.** Current spec uses
   "median observations-per-arm exceeds 50." This is a starting
   heuristic without published validation. Phase 1 should make this
   configurable and revisit empirically after first 6 months of
   operation.

Both items are noted, both have safe defaults, neither blocks Phase 1
shipping.

## Authorship

Drafted by: Claude (Hostile Auditor, Supreme Council)
Brief Date: 2026-04-18
Research Sources: Gemini deep research v1, v2, v3 (audited and
integrated). Specific algorithmic citations: Auer et al. 2002 (UCB1),
Topcuoglu et al. 2002 (HEFT), Tarjan 1972 (SCC), Hutter & Poland
2005 (heterogeneous bandit bound, applicability to CORE's setting
flagged as honest uncertainty).

Sovereign Approval Required: ARCHITECTURE auto-ratify
post-benchmark. Four implementation phase missions follow under E20,
each requiring sovereign signature.

## Footnote 2 — Supersession

This mission supersedes 03_ORCH_E19_004 (Intelligence Router v1).
The predecessor specified the architecture but left two implementation
ambiguities open. Three rounds of focused Socratic Amphitheater
research closed both ambiguities. The v1 mission file in
`prompts/missions/` should be archived to `_graveyard/` rather than
deleted — it documents the design path even though it's superseded.
