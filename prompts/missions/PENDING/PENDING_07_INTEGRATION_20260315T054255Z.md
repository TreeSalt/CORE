# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Contributing Guide + Code of Conduct
DOMAIN: 07_INTEGRATION
TASK: implement_contributing_guide
TYPE: ARCHITECTURE
VERSION: 1.0

## BLUEPRINT
Create two standard GitHub community files:
1. CONTRIBUTING.md — how to contribute to AOS:
   - Fork, branch, propose via mission file
   - All proposals pass benchmark runner
   - Constitutional constraints are non-negotiable
   - Governance domain is human-only
2. CODE_OF_CONDUCT.md — standard Contributor Covenant
   adapted to include the AOS-specific rule that AI agents
   are bound by the same conduct standards as human contributors

## DELIVERABLE
Files: CONTRIBUTING.md, CODE_OF_CONDUCT.md

## CONSTRAINTS
- ARCHITECTURE type — auto-ratifies
- Standard GitHub community health files
- Output valid markdown only
TASK: implement_contributing_guide
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.