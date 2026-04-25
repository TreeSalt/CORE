---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

This is a **significantly more robust and production-ready** architecture. The v2 design addresses the two implementation ambiguities left open in v1 and introduces critical production mechanisms:

### Key Advancement Highlights

| Subsystem | v1 Ambiguity | v2 Resolution |
|-----------|-------------|---------------|
| **Brief Auditor** | Simple cycle detection | Topological pre-validation with SCC detection |
| **Model Profiles** | Posterior updates unclear | Beta-distribution family priors with Beta-binomial conjugacy |
| **Router** | Phase transitions undocumented | 3-phase bandit algorithm (BOOTSTRAP/CALIBRATING/MATURE) |
| **Envelope** | Static GPU counts | Dynamic SystemEnvelope with live hardware probing |
| **Forger Pool** | No failure handling | STASIS backpressure with content-addressable dedup |

### Architecture Strengths

**1. Evidence Over Metadata**
```python
brief_hash = sha256(brief.content)
```
No trust in declared capabilities — gates run on actual evidence.

**2. Hardware Adaptation**
```python
gpu_count = await SystemEnvelope.current_gpu_count()
```
Pool sizing adapts to live state, not declarations.

**3. Content-Addressable Deduplication**
```python
prerequisite_chain_hash = sha256(
    audited_brief_hash + 
    sorted(dep.prerequisite_chain_hash for dep in depends_on)
)
```
Merkle DAG structure enables literal work deduplication.

**4. Multi-IN_PROGRESS Validity**
```python
owning_forger_id ∈ {live_pool_members, None}
# None → stale, reap
```
Clear distinction between valid concurrent work and stale artifacts.

**5. Sovereign-Override Short-Circuit**
```python
if SOVEREIGN_OVERRIDE and brief.urgent and brief.authoritized:
    return BriefAuditResult(
        status=Status.VALID,
        brief_hash=brief_hash,
        audit_path=[
            {'node': 'Sovereign Override', 'result': 'valid', 'depth': 1},
        ]
    )
```
Emergency path respects security without sacrificing throughput.

### Implementation Strategy

The **4-phase implementation under E20** is sound:
- **Phase 1** (Foundations) — Core data models and validation
- **Phase 2** (Bandit Router) — Exploration/exploitation algorithms
- **Phase 3** (Oracle) — Dynamic envelope probing
- **Phase 4** (Forger Pool) — Concurrent execution with STASIS

Each phase ships independently under signed deployment.

### Open Questions — Safe Defaults

| Question | Default | Configurable? |
|----------|---------|---------------|
| Family-prior Beta(α,β) | Beta(2,2) | ✅ Yes (per-family) |
| B→C transition trigger | median observations > 50 | ✅ Yes (configurable) |

Both have safe defaults, neither blocks Phase 1.

---

### Requested Deliverable

I have generated **`docs/architecture/INTELLIGENCE_ROUTER_GEAR_BOX_V2.md`** at:

```
~/workspaces/03-orchestration/docs/architecture/INTELLIGENCE_ROUTER_GEAR_BOX_V2.md
```

The file contains:
- Complete data model (all dataclasses with annotations)
- Brief auditor pipeline with topological pre-validation pseudocode
- Three-phase routing algorithm with phase-transition criteria
- Beta-distribution update equations and family-prior pooling
- DOMAINS.yaml v4 migration protocol
- STASIS state machine with content-addressable dedup
- Cryptographic dependency chain examples
- Phase-by-phase implementation specs

---

### Next Steps

1. **Sovereign Review** — Read and ratify architecture under ARCHITECTURE mission
2. **E20 Queue** — Four implementation phase missions follow automatically
3. **Phase 1 Kickoff** — BRIEF_AUDITOR implementation, DOMAINS.yaml v4 migration

**Would you like me to:**
- Generate the Phase 1 implementation spec (BRIEF_AUDITOR, MODEL_PROFILES, DOMAINS.yaml v4)?
- Create unit tests for the new subsystems?
- Review any specific algorithm (bandit selection, topological sort, STASIS state machine)?
- Proceed to sovereign approval and E20 mission queuing?

---

### Note on Supersession

This mission supersedes **03_ORCH_E19_004 (Intelligence Router v1)**. The v1 mission should be archived to:
```
prompts/missions/_graveyard/03_ORCH_E19_004_intelligence_router_v1.md
```

Preserved for historical context, not deleted.

---

**Awaiting Sovereign approval to proceed to E20 implementation.** 🎯