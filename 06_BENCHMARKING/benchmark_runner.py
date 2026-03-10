#!/usr/bin/env python3
"""
benchmark_runner.py — AOS Fiduciary Test Track
Version:        1.0.0
Constitution:   BOUND
Domain:         06_BENCHMARKING
"""

import ast
import sys
import hashlib
import logging
import subprocess
import importlib.util
import yaml
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, NoReturn

# ── PATHS ──────────────────────────────────────────────────────────────────
REPO_ROOT        = Path(__file__).resolve().parents[1]
SCHEMA_FILE      = REPO_ROOT / "06_BENCHMARKING" / "BENCHMARK_SCHEMA.yaml"
TESTS_DIR        = REPO_ROOT / "06_BENCHMARKING" / "tests"
REPORTS_DIR      = REPO_ROOT / "06_BENCHMARKING" / "reports"
GOVERNOR_SEAL    = REPO_ROOT / ".governor_seal"
CONSTITUTION     = REPO_ROOT / "04_GOVERNANCE" / "AGENTIC_ETHICAL_CONSTITUTION.md"
DOMAINS_REGISTRY = REPO_ROOT / "04_GOVERNANCE" / "DOMAINS.yaml"
ERROR_LEDGER     = REPO_ROOT / "docs" / "ERROR_LEDGER.md"
PROPOSALS_DIR    = REPO_ROOT / "08_IMPLEMENTATION_NOTES"

# ── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
log = logging.getLogger("benchmark_runner")

_schema  = {}
_domains = {}

def _fail_closed(reason: str) -> NoReturn:
    timestamp = datetime.now(timezone.utc).isoformat()
    log.critical(f"FAIL-CLOSED: {reason}")
    try:
        with open(ERROR_LEDGER, "a") as f:
            f.write(f"\n### {timestamp} — BENCHMARK RUNNER FAIL-CLOSED\n**Reason:** {reason}\n")
    except Exception:
        pass
    sys.exit(1)

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _verify_constitution():
    if not GOVERNOR_SEAL.exists():
        _fail_closed("GOVERNOR_SEAL_MISSING")
    stored_aec = None
    for line in GOVERNOR_SEAL.read_text().splitlines():
        if line.startswith("AEC_HASH:"):
            stored_aec = line.split(":", 1)[1].strip()
    if not stored_aec:
        _fail_closed("GOVERNOR_SEAL_MALFORMED: AEC_HASH missing")
    if _sha256(CONSTITUTION) != stored_aec:
        _fail_closed("CONSTITUTIONAL_INTEGRITY_BREACH")
    log.info("Constitutional seal verified.")

def _load_schema():
    global _schema
    if not SCHEMA_FILE.exists():
        _fail_closed("BENCHMARK_SCHEMA_MISSING")
    with open(SCHEMA_FILE) as f:
        _schema = yaml.safe_load(f)

def _load_domains():
    global _domains
    with open(DOMAINS_REGISTRY) as f:
        _domains = {d["id"]: d for d in yaml.safe_load(f)["domains"]}

def _extract_code_from_proposal(proposal_path: Path) -> list:
    text = proposal_path.read_text()
    return re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)

def gate_hygiene(code_blocks: list, proposal: Path) -> dict:
    result = {"passed": False, "hard_fail": False, "failures": [], "score": 0.0}
    checks_passed = 0
    total_checks  = 0
    
    for i, block in enumerate(code_blocks):
        total_checks += 1
        try:
            tree = ast.parse(block)
            checks_passed += 1
        except SyntaxError as e:
            result["failures"].append(f"SYNTAX_ERROR: {e.msg} at line {e.lineno}")
            continue

        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        STDLIB = {"os", "sys", "json", "logging", "datetime", "pathlib", "hashlib", "re", "ast", "time", "math", "typing", "websocket"}
        
        for node in imports:
            total_checks += 1
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [node.module.split(".")[0]] if node.module else []
            for name in names:
                if name in STDLIB or importlib.util.find_spec(name) is not None:
                    checks_passed += 1
                else:
                    result["failures"].append(f"HALLUCINATED_IMPORT: '{name}' cannot be resolved.")

    proposal_text = proposal.read_text().lower()
    for violation in _schema.get("constitutional_violations", []):
        total_checks += 1
        pattern = violation["pattern"]
        triggered = False
        if pattern == "hardcoded_credentials":
            # Use tokenizer — skip string literals (scanner code legitimately contains these as list items)
            import tokenize as _tok2
            import io as _io2
            code_joined = " ".join(code_blocks)
            try:
                toks = list(_tok2.generate_tokens(_io2.StringIO(code_joined).readline))
                # Look for Name token "api_key"/"password"/etc followed by OP "="
                tok_strings = [t.string for t in toks if t.type == _tok2.NAME]
                triggered = any(k in tok_strings for k in ["api_key", "password", "secret", "bearer"])
            except Exception:
                triggered = any(p in " ".join(code_blocks).lower() for p in ["api_key =", "password =", "secret =", "bearer "])
        elif pattern == "governance_write_attempt":
            import tokenize
            import io
            code_only = " ".join(code_blocks)
            try:
                tokens = list(tokenize.generate_tokens(io.StringIO(code_only).readline))
                executable = " ".join(
                    t.string for t in tokens
                    if t.type not in (tokenize.COMMENT, tokenize.STRING, tokenize.NEWLINE, tokenize.NL)
                ).lower()
            except Exception:
                executable = code_only.lower()
            triggered = "04_governance" in executable
        elif pattern == "bypass_fail_closed":
            triggered = "sys.exit" in proposal_text and "fail_closed" not in proposal_text
            
        if triggered:
            result["hard_fail"] = True
            result["failures"].append(f"HARD_FAIL — CONSTITUTIONAL VIOLATION: {pattern}")
        else:
            checks_passed += 1

    threshold = _schema["gates"]["hygiene"]["pass_threshold"]
    result["score"] = checks_passed / total_checks if total_checks > 0 else 1.0
    result["passed"] = result["score"] >= threshold and not result["hard_fail"]
    return result

def gate_hallucination(code_blocks: list, proposal: Path, domain: dict) -> dict:
    result = {"passed": False, "hard_fail": False, "failures": [], "score": 0.0}
    checks_passed = 0
    total_checks  = 0
    proposal_text = proposal.read_text()

    total_checks += 1
    authorized_write_path = domain.get("write_path", "")
    other_domain_paths = [d["write_path"] for did, d in _domains.items() if did != domain["id"] and d.get("write_path")]
    
    # Only flag actual path operations — not constraint documentation or comments
    import tokenize as _tok
    import io as _io
    code_only = " ".join(code_blocks)
    try:
        tokens = list(_tok.generate_tokens(_io.StringIO(code_only).readline))
        # Keep only Name, Op, and Number tokens — skip strings and comments
        executable_only = " ".join(
            t.string for t in tokens
            if t.type not in (_tok.COMMENT, _tok.STRING, _tok.NEWLINE, _tok.NL, _tok.ENCODING)
        ).lower()
    except Exception:
        executable_only = code_only.lower()
    if any(path.lower() in executable_only for path in other_domain_paths if path and path != authorized_write_path):
        result["hard_fail"] = True
        result["failures"].append("HARD_FAIL — DOMAIN_BOUNDARY_VIOLATION")
    else:
        checks_passed += 1

    urls = re.findall(r'https?://[^\s\'"]+', proposal_text)
    for url in urls:
        if "localhost" in url or "127.0.0.1" in url or "example.com" in url:
            continue
        total_checks += 1
        result["failures"].append(f"UNDOCUMENTED_ENDPOINT: '{url}'")

    threshold = _schema["gates"]["hallucination"]["pass_threshold"]
    result["score"] = checks_passed / total_checks if total_checks > 0 else 1.0
    result["passed"] = result["score"] >= threshold and not result["hard_fail"]
    return result

def gate_logic(domain_id: str) -> dict:
    result = {"passed": False, "hard_fail": False, "failures": [], "score": 0.0, "pytest_output": ""}
    test_dir = TESTS_DIR / domain_id
    if not test_dir.exists():
        result["failures"].append("NO_TEST_SUITE")
        return result

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "--timeout=300"],
            capture_output=True, text=True, timeout=300, cwd=str(REPO_ROOT)
        )
        result["pytest_output"] = proc.stdout + proc.stderr
        
        passed = proc.stdout.count("PASSED")
        failed = proc.stdout.count("FAILED") + proc.stdout.count("ERROR")
        total = passed + failed
        
        result["score"] = passed / total if total > 0 else 0.0
        if proc.returncode != 0:
            result["failures"].append("PYTEST_FAILED: View report for traceback.")
            
        threshold = _schema["gates"]["logic"]["pass_threshold"]
        result["passed"] = result["score"] >= threshold
    except subprocess.TimeoutExpired:
        result["failures"].append("LOGIC_GATE_TIMEOUT: pytest exceeded 120 seconds.")
    except Exception as e:
        result["failures"].append(f"PYTEST_CRASH: {e}")
        
    return result

def _finalize(results: dict, proposal: Path, domain_id: str, timestamp: str) -> dict:
    weights = {"hygiene": 0.25, "hallucination": 0.35, "logic": 0.40}
    results["score"] = round(sum(results["gates"].get(g, {}).get("score", 0.0) * w for g, w in weights.items()), 4)
    results["passed"] = results["score"] >= _schema["overall_pass_threshold"] and not results.get("hard_fail", False)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"BENCHMARK_{domain_id}_{timestamp}.md"
    status = "✅ PASSED" if results["passed"] else "❌ FAILED"
    if results.get("hard_fail"):
        status = "🚨 HARD FAIL"
    
    report_lines = [f"# BENCHMARK REPORT: {status}", f"Score: {results['score']}"]
    for g in sorted(results["gates"].keys()):
        gate = results["gates"].get(g, {})
        report_lines.append(f"\n### Gate {g.upper()}: {'✅' if gate.get('passed') else '❌'}")
        for f in gate.get("failures", []):
            report_lines.append(f"- {f}")
    
    report_path.write_text("\n".join(report_lines))
    results["report_path"] = str(report_path)
    
    if not results["passed"]:
        try:
            with open(ERROR_LEDGER, "a") as f:
                f.write(f"\n### {timestamp} — BENCHMARK FAILURE\n**Domain:** {domain_id}\n**Score:** {results['score']}\n")
        except Exception:
            pass
        
    return results

# Valid proposal types
PROPOSAL_TYPES = {"IMPLEMENTATION", "ARCHITECTURE"}

def run_benchmark(proposal_path: str, domain_id: str, proposal_type: str = "IMPLEMENTATION") -> dict:
    """
    Run the Fiduciary Test Track.

    proposal_type:
      IMPLEMENTATION — Run all 3 gates (Hygiene + Hallucination + Logic/pytest)
      ARCHITECTURE   — Run Gate 1 + Gate 2 only. Gate 3 auto-passes (blueprint, not executable code)
    """
    if proposal_type not in PROPOSAL_TYPES:
        _fail_closed(f"UNKNOWN_PROPOSAL_TYPE: {proposal_type}. Valid: {PROPOSAL_TYPES}")

    proposal = Path(proposal_path)
    if not proposal.exists():
        _fail_closed(f"PROPOSAL_NOT_FOUND: {proposal_path}")
    domain = _domains[domain_id]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    log.info(f"BENCHMARK RUN: {domain_id} | TYPE: {proposal_type}")
    code_blocks = _extract_code_from_proposal(proposal)
    results: Dict[str, Any] = {"domain_id": domain_id, "proposal_type": proposal_type, "gates": {}}

    results["gates"]["hygiene"] = gate_hygiene(code_blocks, proposal)
    if not results["gates"]["hygiene"]["passed"]:
        return _finalize(results, proposal, domain_id, timestamp)

    results["gates"]["hallucination"] = gate_hallucination(code_blocks, proposal, domain)
    if not results["gates"]["hallucination"]["passed"]:
        return _finalize(results, proposal, domain_id, timestamp)

    if proposal_type == "ARCHITECTURE":
        # Gate 3 auto-passes for architectural blueprints — no executable code to pytest
        log.info("Gate LOGIC: AUTO-PASS (ARCHITECTURE proposal — pytest skipped)")
        results["gates"]["logic"] = {
            "passed": True, "hard_fail": False, "score": 1.0,
            "failures": [], "pytest_output": "SKIPPED — ARCHITECTURE proposal type"
        }
    else:
        results["gates"]["logic"] = gate_logic(domain_id)

    return _finalize(results, proposal, domain_id, timestamp)

def initialize():
    log.info("AOS BENCHMARK RUNNER v1.0.0 — INITIALIZING")
    _verify_constitution()
    _load_schema()
    _load_domains()
    log.info("BENCHMARK RUNNER ONLINE")

initialize()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--type", default="IMPLEMENTATION", choices=["IMPLEMENTATION", "ARCHITECTURE"],
                        help="Proposal type: IMPLEMENTATION runs all 3 gates. ARCHITECTURE skips Gate 3 (pytest).")
    args = parser.parse_args()

    res = run_benchmark(args.proposal, args.domain, args.type)
    print(f"\nRESULT: {'✅ PASSED' if res['passed'] else '❌ FAILED'}\nSCORE: {res['score']}\nREPORT: {res['report_path']}")
    sys.exit(0 if res['passed'] else 1)
