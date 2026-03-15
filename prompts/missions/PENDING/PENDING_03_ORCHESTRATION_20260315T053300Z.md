# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Update DOMAINS.yaml — Qwen 3.5 Model Roster
DOMAIN: 03_ORCHESTRATION
TASK: update_domains_model_roster
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The sovereign has downloaded Qwen 3.5 models. The model roster in
DOMAINS.yaml and the semantic router must be updated to reflect the
new 4-tier hierarchy.

## BLUEPRINT
Update 04_GOVERNANCE/DOMAINS.yaml to reflect:

Tier FLASH: qwen3.5:4b (3.4 GB) — syntax checks, linting, simple routing
Tier SPRINT: qwen3.5:9b (6.6 GB) — code generation, mission routing
Tier HEAVY: qwen3.5:27b (17 GB) — strategy implementation, complex reasoning
  Alternate: qwen3-coder:30b (18 GB) for code-specific tasks
Tier SUPREME: qwen3.5:35b (23 GB) — architecture proposals, alpha synthesis
Tier COUNCIL: claude.ai — sovereign review, governance decisions

Also update the domain-to-tier mappings:
  00_PHYSICS_ENGINE: heavy (qwen3.5:27b or qwen3-coder:30b)
  01_DATA_INGESTION: sprint (qwen3.5:9b)
  02_RISK_MANAGEMENT: heavy (qwen3.5:27b)
  03_ORCHESTRATION: sprint (qwen3.5:9b)
  05_REPORTING: flash (qwen3.5:4b)
  06_BENCHMARKING: sprint (qwen3.5:9b)
  07_INTEGRATION: council (claude.ai)
  08_CYBERSECURITY: heavy (qwen3.5:27b)

Update orchestration/VRAM_STATE.json model sizes accordingly.

## DELIVERABLE
Patch to 04_GOVERNANCE/DOMAINS.yaml and orchestration/VRAM_STATE.json

## CONSTRAINTS
- Preserve existing domain security classifications
- Preserve cloud/local eligibility flags
- Output valid YAML only
TASK: update_domains_model_roster
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.