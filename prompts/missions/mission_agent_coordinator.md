MISSION: Implement AgentCoordinator
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — WHAT ALREADY EXISTS:
- orchestration/semantic_router.py v3.0.0 — routes tasks to models by domain
- scripts/run_loop.py — autonomous factory agent
- 04_GOVERNANCE/DOMAINS.yaml — domain security classes and model assignments
- 02_RISK_MANAGEMENT/risk_management/risk_manager.py — RiskManager (just implemented)

REQUIREMENTS:
Implement AgentCoordinator in 03_ORCHESTRATION/orchestration_domain/agent_coordinator.py

The class ALREADY EXISTS as a stub. Implement it to:
- accept task packages: {domain, task, mission, model, tier}
- track active agent assignments per domain (one agent per domain at a time)
- queue tasks when a domain is busy (use collections.deque)
- enforce domain lock: reject new assignment if domain already has active agent
- log all assignment events: ASSIGNED, COMPLETED, QUEUED, REJECTED
- release domain lock on task completion or failure
- expose next_task() -> dict | None for the run_loop to poll
- FAIL-CLOSED: raise CoordinatorError on any constraint breach

INTERFACE CONTRACT:
- assign(task_package: dict) -> str (returns task_id)
- complete(task_id: str) -> None
- fail(task_id: str, reason: str) -> None
- next_task() -> dict | None
- get_active_assignments() -> dict
- get_queue_depth(domain: str) -> int

CONSTRAINTS:
- stdlib only
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Thread-safe (use threading.Lock for domain locks)
- CoordinatorError must be importable from this module
