# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: Design an AgentCoordinator class for the 03_ORCHESTRATION domain. It must: accept task packages from the semantic router, track active agent assignments per domain, enforce that no domain runs more than one active agent at a time, queue tasks when a domain is busy, and log all assignment and completion events. No hardcoded credentials. No governance domain writes. Fail closed on constraint breach.
TASK: implement_agent_coordinator
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.