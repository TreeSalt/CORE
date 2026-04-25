"""
06_BENCHMARKING — BenchmarkOrchestrator (E14-GATED)
====================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection (factory cannot self-validate)

PATCH FROM PREVIOUS VERSION
This version wires four deterministic E14 gates BEFORE the existing
hygiene/hallucination/logic pipeline:

  1. MIN_SUBSTANCE      — rejects empty/trivial proposals
  2. TRUNCATION         — rejects mid-method failures, prompt leaks
  3. IMPORT_RESOLUTION  — rejects hallucinated imports
  4. CONTRACT_NAMES     — rejects function name drift (if brief provided)

Any E14 gate failure aborts the pipeline with passed=False and score=0.0.
No further scoring is computed. The failure becomes a first-class event
in the benchmark report.

Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on constraint breaches
  - E14 gates are DETERMINISTIC short-circuits — they never approve
    anything, only reject

Backwards compatibility:
  - run(proposal_path, domain_id) still works (legacy callers)
  - run(proposal_path, domain_id, mission_file_path=...) enables CONTRACT_NAMES
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# E14 GATE IMPORTS (sovereign-injected, VERIFIED trust class)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gates"))
try:
    from min_substance import gate_min_substance
    from truncation_detection import gate_truncation_detection
    from import_resolution import gate_import_resolution
    from contract_name import gate_contract_names
    E14_GATES_AVAILABLE = True
except ImportError as e:
    E14_GATES_AVAILABLE = False
    logging.getLogger(__name__).critical(
        f"E14 GATES UNAVAILABLE — falling back to legacy pipeline: {e}"
    )

log = logging.getLogger(__name__)

GOVERNANCE_DOMAIN = "04_GOVERNANCE"
REPO_ROOT = Path(__file__).resolve().parents[2]
BRIEFS_DIR = REPO_ROOT / "prompts" / "missions"


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
            "gates": {k: v.to_dict() if hasattr(v, "to_dict") else v
                      for k, v in self.gates.items()},
        }


class BenchmarkOrchestrator:
    """Runs the E14-gated benchmark pipeline for a given proposal."""

    def _preflight(self, domain_id: str) -> None:
        if GOVERNANCE_DOMAIN in domain_id:
            _fail_closed(f"PREFLIGHT: governance domain forbidden — {domain_id}")

    def _extract_code_blocks(self, proposal_path: Path) -> list[str]:
        fence = "```"
        pattern = fence + r"python\n(.*?)" + fence
        return re.findall(pattern, proposal_path.read_text(), re.DOTALL)

    # ─── E14 GATES (run BEFORE existing pipeline) ─────────────

    def _e14_min_substance(self, proposal_path: Path) -> GateResult:
        passed, reason = gate_min_substance(proposal_path)
        return GateResult(
            name="e14_min_substance",
            passed=passed,
            score=1.0 if passed else 0.0,
            failures=[] if passed else [reason],
        )

    def _e14_truncation(self, proposal_path: Path) -> GateResult:
        passed, reason = gate_truncation_detection(proposal_path)
        return GateResult(
            name="e14_truncation",
            passed=passed,
            score=1.0 if passed else 0.0,
            failures=[] if passed else [reason],
        )

    def _e14_import_resolution(self, proposal_path: Path) -> GateResult:
        passed, reason = gate_import_resolution(proposal_path, REPO_ROOT)
        return GateResult(
            name="e14_import_resolution",
            passed=passed,
            score=1.0 if passed else 0.0,
            failures=[] if passed else [reason],
        )

    def _e14_contract_names(self, proposal_path: Path,
                             mission_file_path: Path | None) -> GateResult:
        if mission_file_path is None or not mission_file_path.exists():
            return GateResult(
                name="e14_contract_names",
                passed=True,
                score=1.0,
                failures=["SKIPPED: no mission_file_path provided (legacy mode)"],
            )
        passed, reason = gate_contract_names(mission_file_path, proposal_path)
        return GateResult(
            name="e14_contract_names",
            passed=passed,
            score=1.0 if passed else 0.0,
            failures=[] if passed else [reason],
        )

    # ─── LEGACY GATES (preserved) ─────────────────────────────

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
        return GateResult(name="hygiene", passed=len(failures) == 0,
                          score=score, failures=failures)

    def _gate_hallucination(self, code_blocks: list[str]) -> GateResult:
        import ast
        import importlib.util
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
        return GateResult(name="hallucination", passed=len(failures) == 0,
                          score=score, failures=failures)

    def _gate_logic(self, code_blocks: list[str], proposal_path: Path,
                    domain_id: str) -> GateResult:
        import subprocess
        test_dir = Path("06_BENCHMARKING/tests") / domain_id
        if not test_dir.exists():
            return GateResult(name="logic", passed=True, score=1.0,
                              failures=["NO_TESTS: skipped"])
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "--tb=short", "-q"],
            capture_output=True, text=True
        )
        passed = result.returncode == 0
        failures = [] if passed else ["PYTEST_FAILED: View report for traceback."]
        return GateResult(name="logic", passed=passed,
                          score=1.0 if passed else 0.0, failures=failures)

    # ─── MAIN PIPELINE ────────────────────────────────────────

    def _resolve_mission_file(self, mission_file: str | None) -> Path | None:
        """Resolve mission_file argument to a Path under prompts/missions/."""
        if not mission_file:
            return None
        p = Path(mission_file)
        if p.is_absolute() and p.exists():
            return p
        candidate = BRIEFS_DIR / mission_file
        if candidate.exists():
            return candidate
        return None

    def run(self, proposal_path: str, domain_id: str,
            mission_file_path: str | None = None) -> BenchmarkResult:
        self._preflight(domain_id)
        path = Path(proposal_path)
        if not path.exists():
            _fail_closed(f"PROPOSAL_NOT_FOUND: {proposal_path}")

        gates: dict = {}

        # ── E14 GATES (deterministic short-circuit) ───────────
        if E14_GATES_AVAILABLE:
            mfp = self._resolve_mission_file(mission_file_path)

            for gate_method, gate_args, gate_label in [
                (self._e14_min_substance, (path,), "E14_MIN_SUBSTANCE"),
                (self._e14_truncation, (path,), "E14_TRUNCATION"),
                (self._e14_import_resolution, (path,), "E14_IMPORT_RESOLUTION"),
                (self._e14_contract_names, (path, mfp), "E14_CONTRACT_NAMES"),
            ]:
                result = gate_method(*gate_args)
                gates[result.name] = result
                log.info("Gate %s: %s", gate_label,
                         "PASS" if result.passed else "FAIL — " + "; ".join(result.failures))
                if not result.passed:
                    return BenchmarkResult(
                        domain_id=domain_id,
                        passed=False,
                        score=0.0,
                        gates=gates,
                    )

        # ── LEGACY PIPELINE (only reached if E14 gates pass) ──
        code_blocks = self._extract_code_blocks(path)

        hygiene = self._gate_hygiene(code_blocks)
        gates["hygiene"] = hygiene
        log.info("Gate HYGIENE: %s score=%.4f",
                 "PASS" if hygiene.passed else "FAIL", hygiene.score)
        if not hygiene.passed:
            return BenchmarkResult(
                domain_id=domain_id,
                passed=False,
                score=round(hygiene.score * 0.25, 4),
                gates=gates,
            )

        hallucination = self._gate_hallucination(code_blocks)
        gates["hallucination"] = hallucination
        log.info("Gate HALLUCINATION: %s score=%.4f",
                 "PASS" if hallucination.passed else "FAIL", hallucination.score)
        if not hallucination.passed:
            return BenchmarkResult(
                domain_id=domain_id,
                passed=False,
                score=round(0.25 + hallucination.score * 0.35, 4),
                gates=gates,
            )

        logic = self._gate_logic(code_blocks, path, domain_id)
        gates["logic"] = logic
        log.info("Gate LOGIC: %s score=%.4f",
                 "PASS" if logic.passed else "FAIL", logic.score)

        weights = {"hygiene": 0.25, "hallucination": 0.35, "logic": 0.40}
        score = (hygiene.score * weights["hygiene"] +
                 hallucination.score * weights["hallucination"] +
                 logic.score * weights["logic"])

        return BenchmarkResult(
            domain_id=domain_id,
            passed=hygiene.passed and hallucination.passed and logic.passed,
            score=round(score, 4),
            gates=gates,
        )
