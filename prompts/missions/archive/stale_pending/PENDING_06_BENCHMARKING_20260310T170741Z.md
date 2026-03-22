# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 06_BENCHMARKING
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 06_BENCHMARKING
SECURITY_CLASS: INTERNAL
MISSION: MISSION: Fix BenchmarkOrchestrator _gate_logic traceback reporting
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — EXISTING FILE:
06_BENCHMARKING/benchmarking_domain/benchmark_orchestrator.py

The _gate_logic method currently returns this on failure:
  failures=["PYTEST_FAILED: View report for traceback."]

This is useless. The run_loop.py analyze_failures() function needs the actual
pytest output to generate actionable corrective context for retry attempts.
Without real tracebacks, the factory retries blindly and wastes 32b inference time.

WHAT TO FIX:
Replace the _gate_logic method body with one that:
- captures both stdout and stderr from the pytest subprocess
- extracts FAILED lines, AssertionError lines, and the short traceback block
- stores captured output in the GateResult failures list (up to 3000 chars)
- includes the actual pytest exit code in the failure message
- still returns passed=True if returncode == 0

The fixed method signature stays identical:
  def _gate_logic(self, code_blocks, proposal_path, domain_id) -> GateResult

REFERENCE IMPLEMENTATION PATTERN (already working in benchmark_runner.py):
  result = subprocess.run([...], capture_output=True, text=True, timeout=300)
  output = result.stdout + result.stderr
  # Extract meaningful lines:
  meaningful = [l for l in output.splitlines()
                if any(kw in l for kw in ["FAILED", "ERROR", "AssertionError",
                                           "assert ", "short test summary"])]
  failures = [f"PYTEST_FAILED (rc={result.returncode}):"] + meaningful[:20]
  if len(output) > 500:
      failures.append(output[-2000:])  # tail of output for context

CONSTRAINTS:
- stdlib only
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Do not change any other method — only _gate_logic
- subprocess timeout must be 300s (not default)
- Output the complete updated file, not a diff
TASK: fix_gate_logic_traceback_reporting
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.