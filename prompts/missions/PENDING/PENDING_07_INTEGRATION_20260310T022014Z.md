# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: Design an IntegrationAgent class for the 07_INTEGRATION domain. It must: accept two proposal files from different domains, verify their interfaces are compatible (method signatures, data structures), flag any interface mismatches, and produce a structured compatibility report. No hardcoded credentials. No governance domain writes. Fail closed on constraint breach.
TASK: implement_integration_agent
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.