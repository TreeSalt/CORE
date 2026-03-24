# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
TASK: 07_INTEG_E3_001_smoke_test_v2
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only

--- MISSION BRIEF ---



INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.