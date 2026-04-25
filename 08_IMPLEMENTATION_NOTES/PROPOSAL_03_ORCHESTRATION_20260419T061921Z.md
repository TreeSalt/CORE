---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

# Architecture Document Received — E19_005 INTELLIGENCE_ROUTER_GEAR_BOX_V2

Thank you for submitting this comprehensive architecture document. This represents a significant advancement over the v1 design, resolving previously open ambiguities and introducing substantial architectural improvements.

## Design Summary

| Subsystem | Core Innovation | Status |
|-----------|-----------------|--------|
| **Brief Auditor** | Topological pre-validation + Merkle DAG dedup | Ready for Phase 1 |
| **Model Profiler** | Beta-distribution posteriors with family-level priors | Ready for Phase 1 |
| **Bandit Router** | Three-phase routing (BOOTSTRAP/CALIBRATING/MATURE) | Ready for Phase 2 |
| **Oracle** | JSON validation + content-addressable dispatch plans | Ready for Phase 3 |
| **Forger Pool** | STASIS backpressure + BATCHER deduplication | Ready for Phase 4 |

## Key Architectural Advancements

### 1. **Brief Auditor v2**
The topological pre-validation using Tarjan's SCC algorithm is a significant improvement over the v1 design. The Merkle DAG structure with `prerequisite_chain_hash` enables content-addressable deduplication across dependent subtasks.

### 2. **Model Profiler**
The Beta-distribution family prior pooling allows new models to bootstrap effectively when domain-level observation counts are low. This solves the "cold-start" problem that plagues single-domain profiling.

### 3. **Bandit Router**
The three-phase routing design is particularly elegant:

- **BOOTSTRAP**: UCB1 for guaranteed exploration (τ = 500)
- **CALIBRATING**: Hybrid exploration with HEFT cost awareness
- **MATURE**: Thompson Sampling with family priors + SOVEREIGN_OVERRIDE

### 4. **Forger Pool STASIS**
The STASIS backpressure mechanism is well-documented. The content-addressable deduplication prevents redundant work on dependent subtasks sharing the same `prerequisite_chain_hash`.

### 5. **Multi-IN_PROGRESS Validity**
The distinction between owned vs. unowned IN_PROGRESS missions is crucial for the `core doctor` and `core stop --reap` operations.

## Open Questions Requiring Sovereign Attention

### Question 1: Family-Prior Initial Values
The spec uses Beta(2,2) as the family-prior starting point. You've noted this should be configurable per-family in Phase 1. **Recommendation:** Add `families.yaml` with:
```yaml
families:
  - name: reasoning
    prior_mean: 0.7
    prior_std: 0.2
    family_type: "reasoning-heavy"
  - name: coding
    prior_mean: 0.65
    prior_std: 0.15
    family_type: "coding-heavy"
```

### Question 2: B→C Transition Trigger
The "median observations-per-arm > 50" heuristic needs validation. **Recommendation:** Make this configurable and add empirical monitoring after first 6 months.

## Implementation Recommendations

### Phase 1 Dependencies
1. **Topological Pre-validation Test**
   - Implement cycle detection using Tarjan's SCC
   - Test cases: valid DAG, cycles, self-loops, missing prerequisites

2. **Beta-Distribution Update**
   - Implement posterior updates per-domain arm
   - Test family-prior pooling when observation counts are low

### Phase 2 Dependencies
1. **Bandit Router State Machine**
   - Phase transitions need clear, testable criteria
   - SOVEREIGN_OVERRIDE needs to be tested with manual trigger

2. **Exploration Ratio Tracking**
   - Track arm-level exploration counts
   - Implement phase-transition logging

### Phase 3 Dependencies
1. **Oracle JSON Validation**
   - Implement dataclass schema validation
   - Test fallback path when validation fails

2. **DispatchPlan Hash Computation**
   - Implement prerequisite_chain_hash computation
   - Test with multi-level dependencies

### Phase 4 Dependencies
1. **VRAM-Aware Pool Sizing**
   - Implement live VRAM probing
   - Test concurrency cap enforcement

2. **Content-Addressable Dedup**
   - Group by prerequisite_chain_hash
   - Test deduplication with identical subtasks

## Sovereign Decision Required

Before implementation phases can proceed, the Sovereign needs to decide:

1. **Ratify Architecture v2** → Enables E20 implementation mission queue
2. **Archive E19_004 to Graveyard** → Document the v1-to-v2 design path
3. **Configure Family Priors** → Provide initial configuration for families.yaml
4. **Set Transition Heuristics** → Configure observation-count thresholds

## Next Steps

1. **Review** the architecture document (10-15 minutes)
2. **Sign Off** on E20 implementation mission
3. **Configure** family priors and transition heuristics
4. **Execute** Phase 1 → Phase 4 implementation sequence
5. **Monitor** for 6 months, revisit B→C transition heuristic

## Questions for the Sovereign

1. **Family Prior Configuration:** Should we ship with Beta(2,2) defaults or allow empty families.yaml with per-family configuration in Phase 1?

2. **Transition Heuristics:** What observation-count thresholds do you recommend for BOOTSTRAP→CALIBRATING and CALIBRATING→MATURE transitions?

3. **Phase Execution Order:** Should all phases execute sequentially (current recommendation) or can phases be parallelized?

4. **Graveyard Access:** Should we keep the E19_004 v1 mission in graveyard for historical reference or archive it?

5. **Benchmark Requirements:** What benchmark criteria will be used to auto-ratify after E20 implementation?

---

**Recommendation:** Proceed with ratification and Phase 1 implementation, with family priors configurable in Phase 1. The architecture is sound and the implementation phases are well-defined.

**Status:** ✅ Ready for Sovereign Signature

Would you like me to:
1. **Draft the Sovereign signature request** for E20?
2. **Generate Phase 1 implementation specification** in detail?
3. **Create test plan** for all four phases?
4. **Configure initial families.yaml** for Phase 1?

What would you like to proceed with?