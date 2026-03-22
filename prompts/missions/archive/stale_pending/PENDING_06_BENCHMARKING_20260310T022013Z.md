# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 06_BENCHMARKING
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 06_BENCHMARKING
SECURITY_CLASS: INTERNAL
MISSION: Design a BenchmarkOrchestrator class for the 06_BENCHMARKING domain. It must: accept a proposal file path and domain ID, run the three-gate pipeline (hygiene, hallucination, logic), return a structured result dict with gate scores and overall pass/fail, and log all gate results. No hardcoded credentials. No governance domain writes. Fail closed on constraint breach.
TASK: implement_benchmark_orchestrator
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.