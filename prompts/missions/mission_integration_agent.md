MISSION: Implement IntegrationAgent
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — PRODUCTION MODULES TO VERIFY AGAINST:
The following modules are live — IntegrationAgent must verify new proposals
are interface-compatible with these:
- DataMultiplexer (01_DATA_INGESTION) — normalize(data) -> dict
- RiskManager (02_RISK_MANAGEMENT) — approve_trade(instrument, quantity, loss) -> bool
- AgentCoordinator (03_ORCHESTRATION) — assign(task_package) -> str
- BenchmarkOrchestrator (06_BENCHMARKING) — run(proposal, domain, type) -> dict

REQUIREMENTS:
Implement IntegrationAgent in 07_INTEGRATION/integration_domain/integration_agent.py

The class ALREADY EXISTS as a stub. Implement it to:
- accept two proposal file paths from different domains
- extract class/method signatures using ast.parse (stdlib AST, no exec)
- verify interfaces are compatible:
  - method names match expected interface contracts
  - argument counts are compatible
  - return type annotations are consistent where present
- produce structured compatibility report:
  {
    "compatible": bool,
    "domain_a": str,
    "domain_b": str,
    "matches": list[str],
    "mismatches": list[str],
    "warnings": list[str],
    "timestamp": str
  }
- flag mismatches but do NOT block — return report, let sovereign decide
- log all verification events to ERROR_LEDGER format

INTERFACE CONTRACT:
- verify(proposal_a: str, proposal_b: str) -> dict
- verify_against_production(proposal: str, domain: str) -> dict
- get_last_report() -> dict | None

CONSTRAINTS:
- stdlib only (ast, pathlib, logging, datetime)
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Use ast.parse — never eval() or exec()
