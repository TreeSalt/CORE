---
STATUS: RATIFIED
---

```python
"""
06_BENCHMARKING — BenchmarkOrchestrator
OOP wrapper over the three-gate benchmark pipeline.
Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on constraint breaches
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

GOVERNANCE_DOMAIN = "04_GOVERNANCE"


def _fail_closed(reason: str) -> None:
    log.critical("FAIL-CLOSED | %s", reason)
    sys.exit(1)


@dataclass
class GateResult:
    name: str
    passed: bool
    score: float
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "failures": self.failures,
        }


@dataclass
class BenchmarkResult:
    domain_id: str
    passed: bool
    score: float
    gates: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "domain_id": self.domain_id,
            "passed": self.passed,
            "score": self.score,
            "gates": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.gates.items()},
        }


class BenchmarkOrchestrator:
    """Runs the three-gate benchmark pipeline for a given proposal."""

    def _preflight(self, domain_id: str) -> None:
        if GOVERNANCE_DOMAIN in domain_id:
            _fail_closed(f"PREFLIGHT: governance domain forbidden — {domain_id}")

    def _extract_code_blocks(self, proposal_path: Path) -> list[str]:
        fence = "```"
        pattern = fence + r"python\n(.*?)" + fence
        return re.findall(pattern, proposal_path.read_text(), re.DOTALL)

    def _gate_hygiene(self, code_blocks: list[str]) -> GateResult:
        import ast
        failures = []
        passed_checks = 0
        total_checks = 0
        for block in code_blocks:
            total_checks += 1
            try:
                ast.parse(block)
                passed_checks += 1
            except SyntaxError as e:
                failures.append(f"SYNTAX_ERROR: {e}")
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        return GateResult(name="hygiene", passed=len(failures) == 0, score=score, failures=failures)

    def _gate_hallucination(self, code_blocks: list[str]) -> GateResult:
        import ast, importlib.util
        failures = []
        passed = 0
        total = 0
        STDLIB = {"os", "sys", "json", "logging", "datetime", "pathlib",
                  "hashlib", "re", "ast", "time", "math", "typing",
                  "dataclasses", "threading", "collections", "itertools"}
        for block in code_blocks:
            try:
                tree = ast.parse(block)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = ([a.name.split(".")[0] for a in node.names]
                             if isinstance(node, ast.Import)
                             else ([node.module.split(".")[0]] if node.module else []))
                    for name in names:
                        total += 1
                        if name in STDLIB or importlib.util.find_spec(name) is not None:
                            passed += 1
                        else:
                            failures.append(f"HALLUCINATED_IMPORT: '{name}'")
        score = passed / total if total > 0 else 1.0
        return GateResult(name="hallucination", passed=len(failures) == 0, score=score, failures=failures)

    def _gate_logic(self, code_blocks: list[str], proposal_path: Path, domain_id: str) -> GateResult:
        import subprocess, tempfile, os
        test_dir = Path("06_BENCHMARKING/tests") / domain_id
        if not test_dir.exists():
            return GateResult(name="logic", passed=True, score=1.0, failures=["NO_TESTS: skipped"])
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "--tb=short", "-q"],
            capture_output=True, text=True
        )
        passed = result.returncode == 0
        failures = [] if passed else ["PYTEST_FAILED: View report for traceback."]
        return GateResult(name="logic", passed=passed, score=1.0 if passed else 0.0, failures=failures)

    def run(self, proposal_path: str, domain_id: str) -> BenchmarkResult:
        self._preflight(domain_id)
        path = Path(proposal_path)
        if not path.exists():
            _fail_closed(f"PROPOSAL_NOT_FOUND: {proposal_path}")

        code_blocks = self._extract_code_blocks(path)

        hygiene = self._gate_hygiene(code_blocks)
        log.info("Gate HYGIENE: %s score=%.4f", "PASS" if hygiene.passed else "FAIL", hygiene.score)
        if not hygiene.passed:
            return BenchmarkResult(
                domain_id=domain_id,
                passed=False,
                score=round(hygiene.score * 0.25, 4),
                gates={"hygiene": hygiene}
            )

        hallucination = self._gate_hallucination(code_blocks)
        log.info("Gate HALLUCINATION: %s score=%.4f", "PASS" if hallucination.passed else "FAIL", hallucination.score)
        if not hallucination.passed:
            return BenchmarkResult(
                domain_id=domain_id,
                passed=False,
                score=round(0.25 + hallucination.score * 0.35, 4),
                gates={"hygiene": hygiene, "hallucination": hallucination}
            )

        logic = self._gate_logic(code_blocks, path, domain_id)
        log.info("Gate LOGIC: %s score=%.4f", "PASS" if logic.passed else "FAIL", logic.score)

        weights = {"hygiene": 0.25, "hallucination": 0.35, "logic": 0.40}
        score = (hygiene.score * weights["hygiene"] +
                 hallucination.score * weights["hallucination"] +
                 logic.score * weights["logic"])

        return BenchmarkResult(
            domain_id=domain_id,
            passed=hygiene.passed and hallucination.passed and logic.passed,
            score=round(score, 4),
            gates={"hygiene": hygiene, "hallucination": hallucination, "logic": logic}
        )

```
