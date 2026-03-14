# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: AOS Boundary Audit — Engine vs Payload Classification
DOMAIN: 07_INTEGRATION
TASK: implement_boundary_audit
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, Phase 3 requires splitting the monorepo into AOS (open-source
engine) and TRADER_OPS (commercial payload). Before that split can happen,
every file must be classified as ENGINE or PAYLOAD.

## BLUEPRINT
Create AOS_BOUNDARY_AUDIT.md that:
1. Lists every directory in the repo
2. Classifies each as ENGINE (goes to AOS) or PAYLOAD (stays in TRADER_OPS)
3. Identifies SHARED files that both repos need (e.g., base classes)
4. Documents extraction strategy: git subtree split commands
5. Lists files that need refactoring before split (tight coupling)

Classification rules:
- 04_GOVERNANCE/ → ENGINE (universal governance)
- 03_ORCHESTRATION/ → ENGINE (universal orchestration)
- 06_BENCHMARKING/ → ENGINE (universal benchmarking)
- 08_CYBERSECURITY/ → ENGINE (universal security)
- 00_PHYSICS_ENGINE/ → PAYLOAD (trading-specific)
- 01_DATA_INGESTION/ → PAYLOAD (market data specific)
- antigravity_harness/strategies/ → PAYLOAD
- antigravity_harness/execution/ → PAYLOAD
- antigravity_harness/instruments/ → PAYLOAD
- scripts/ → MIXED (some engine, some payload)

## DELIVERABLE
File: docs/AOS_BOUNDARY_AUDIT.md

## CONSTRAINTS
- ARCHITECTURE proposal — document, not code
- Must cover every top-level directory
- Must identify tight coupling points
- Output valid markdown only
TASK: implement_boundary_audit
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.