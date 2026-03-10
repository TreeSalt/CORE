MISSION: Implement BenchmarkOrchestrator
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — WHAT ALREADY EXISTS:
- 06_BENCHMARKING/benchmark_runner.py v1.0.0 — three-gate pipeline already operational
  - Gate 1: HALLUCINATION (import resolution)
  - Gate 2: HYGIENE (constitutional compliance)
  - Gate 3: LOGIC (pytest execution)
- 06_BENCHMARKING/BENCHMARK_SCHEMA.yaml v1.1 — schema definition

KEY LESSON FROM PRODUCTION:
- ARCHITECTURE proposals must skip Gate 3 (pytest) — they produce markdown, not code
- Local domain packages (e.g. data_ingestion, risk_management) must not trigger
  HALLUCINATED_IMPORT — they are local, not PyPI packages
- Gate 3 subprocess timeout is 300s (not 120s)
- benchmark_runner.py already stores pytest_output in gate results

REQUIREMENTS:
Implement BenchmarkOrchestrator in 06_BENCHMARKING/benchmarking_domain/benchmark_orchestrator.py

The class ALREADY EXISTS as a stub. Implement it to:
- accept: proposal_path (str), domain_id (str), proposal_type (str)
- run the three-gate pipeline by invoking benchmark_runner.py as subprocess
- parse the benchmark report and return structured result dict:
  {
    "passed": bool,
    "score": float,
    "gates": {"hallucination": bool, "hygiene": bool, "logic": bool},
    "failures": list[str],
    "report_path": str,
    "proposal_type": str
  }
- ARCHITECTURE proposals: logic gate auto-passes, score computed on gates 1+2 only
- log all gate results with timestamps
- FAIL-CLOSED: return passed=False on any subprocess failure

INTERFACE CONTRACT:
- run(proposal_path: str, domain_id: str, proposal_type: str = "IMPLEMENTATION") -> dict
- get_last_result() -> dict | None

CONSTRAINTS:
- stdlib only
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
