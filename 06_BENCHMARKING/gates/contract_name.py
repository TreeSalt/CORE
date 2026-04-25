#!/usr/bin/env python3
"""
CONTRACT_NAME_GATE — Enforce Brief Interface Contracts
========================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection (factory cannot self-validate)

PURPOSE
Catches the failure mode documented across E14_BACKLOG_001 and 002:
both tier_loader_v4 and preflight_runner exhibited FUNCTION_NAME_DRIFT
where the model wrote functions named differently than the brief
specified. The benchmark gate did not detect this because tests against
nonexistent functions produce ImportError or AttributeError at runtime,
which the test harness misclassifies as test failure rather than
contract violation.

This gate parses the brief's INTERFACE CONTRACT section, extracts every
expected name (functions, classes, dataclasses, constants), and walks
the proposal's AST to verify each expected name exists at the module
level. Exact match only — no fuzzy, no substring, no case-insensitive.

CONTRACT NAME EXTRACTION
The gate looks for these patterns in the brief:
- `### Function: name(...)` or `### Function: name`
- `### Dataclass: name`
- `### Class: name`
- Lines under `### Constants` matching `^- ([A-Z_]+) =`
- Module-level assignment patterns in the brief

LEGACY EXEMPTION
If a brief has no `INTERFACE CONTRACT` or `## INTERFACE CONTRACT` section,
the gate passes by default. This protects pre-E14 missions that were
authored before this convention existed. As briefs migrate to the new
canonical schema, this exemption can be removed.
"""

import ast
import re
from pathlib import Path

# Regex patterns for parsing brief INTERFACE CONTRACT sections
FUNCTION_PATTERNS = [
    re.compile(r'^###?\s*Function:\s*([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE),
    re.compile(r'^- \*\*Function:\*\*\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?', re.MULTILINE),
]

CLASS_PATTERNS = [
    re.compile(r'^###?\s*Class:\s*([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE),
    re.compile(r'^###?\s*Dataclass:\s*([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE),
    re.compile(r'^- \*\*Class:\*\*\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?', re.MULTILINE),
    re.compile(r'^- \*\*Dataclass:\*\*\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?', re.MULTILINE),
]

CONSTANT_PATTERNS = [
    # `- CONSTANT_NAME = value` or `- CONSTANT_NAME` under a Constants header
    re.compile(r'^-\s*`?([A-Z][A-Z0-9_]+)`?\s*=', re.MULTILINE),
]

# Section header pattern (case-insensitive)
INTERFACE_SECTION_PATTERN = re.compile(
    r'^##?\s*INTERFACE\s+CONTRACT', re.MULTILINE | re.IGNORECASE
)


def _extract_interface_section(brief_text: str) -> str | None:
    """Find the INTERFACE CONTRACT section and return its content.

    Returns None if no such section exists (legacy brief).
    """
    match = INTERFACE_SECTION_PATTERN.search(brief_text)
    if not match:
        return None

    # Extract from the header to the next ## section (or end of file)
    start = match.end()
    rest = brief_text[start:]
    next_section = re.search(r'^##\s+[A-Z]', rest, re.MULTILINE)
    if next_section:
        return rest[:next_section.start()]
    return rest


def extract_contract_names_from_brief(brief_text: str) -> dict:
    """Parse INTERFACE CONTRACT section, return expected names by category.

    Returns: {"functions": [...], "classes": [...], "constants": [...]}
    Returns empty lists if no INTERFACE CONTRACT section found.
    """
    section = _extract_interface_section(brief_text)
    result = {"functions": [], "classes": [], "constants": []}

    if section is None:
        return result  # Legacy brief, no contract to enforce

    for pattern in FUNCTION_PATTERNS:
        result["functions"].extend(pattern.findall(section))
    for pattern in CLASS_PATTERNS:
        result["classes"].extend(pattern.findall(section))
    for pattern in CONSTANT_PATTERNS:
        result["constants"].extend(pattern.findall(section))

    # Deduplicate while preserving order
    for key in result:
        result[key] = list(dict.fromkeys(result[key]))

    return result


def extract_defined_names_from_code(code: str) -> dict:
    """Walk AST to find all module-level definitions.

    Returns: {"functions": [...], "classes": [...], "constants": [...]}
    """
    result = {"functions": [], "classes": [], "constants": []}

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return result

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    # Constants are ALL_CAPS by convention
                    if name.isupper() or (name.replace("_", "").isupper()
                                           and "_" in name):
                        result["constants"].append(name)

    return result


def gate_contract_names(brief_path: Path,
                         proposal_path: Path) -> tuple[bool, str]:
    """Wrapper for benchmark runner integration.

    Returns (passed: bool, reason: str). Reason lists missing names
    grouped by category.
    """
    brief = Path(brief_path)
    proposal = Path(proposal_path)

    if not brief.exists():
        return (False, f"CONTRACT_GATE_FAIL: brief not found at {brief_path}")
    if not proposal.exists():
        return (False, f"CONTRACT_GATE_FAIL: proposal not found at {proposal_path}")

    try:
        brief_text = brief.read_text()
    except Exception as e:
        return (False, f"CONTRACT_GATE_FAIL: cannot read brief: {e}")

    expected = extract_contract_names_from_brief(brief_text)
    total_expected = (len(expected["functions"]) +
                      len(expected["classes"]) +
                      len(expected["constants"]))

    if total_expected == 0:
        # Legacy brief with no enforceable contract — pass by default
        return (True, "")

    try:
        proposal_text = proposal.read_text()
    except Exception as e:
        return (False, f"CONTRACT_GATE_FAIL: cannot read proposal: {e}")

    # Extract code from proposal (largest valid block)
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', proposal_text, re.DOTALL)
    blocks = [b.strip() for b in blocks if b.strip()]
    valid_blocks = []
    for block in blocks:
        try:
            ast.parse(block)
            valid_blocks.append(block)
        except SyntaxError:
            continue

    if not valid_blocks:
        return (False,
                "CONTRACT_GATE_FAIL: no syntactically valid code blocks "
                "in proposal to check against contract")

    code = max(valid_blocks, key=len)
    defined = extract_defined_names_from_code(code)

    # Compare exact names — no fuzzy matching
    missing = {"functions": [], "classes": [], "constants": []}
    for category in ("functions", "classes", "constants"):
        for name in expected[category]:
            if name not in defined[category]:
                missing[category].append(name)

    total_missing = sum(len(v) for v in missing.values())
    if total_missing == 0:
        return (True, "")

    parts = []
    if missing["functions"]:
        parts.append(f"functions: {missing['functions']}")
    if missing["classes"]:
        parts.append(f"classes: {missing['classes']}")
    if missing["constants"]:
        parts.append(f"constants: {missing['constants']}")
    detail = "; ".join(parts)

    return (False,
            f"CONTRACT_GATE_FAIL: proposal missing {total_missing} expected "
            f"name(s) — {detail}")


# ─── CLI for standalone testing ──────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 contract_name.py <brief_path> <proposal_path>")
        sys.exit(2)
    passed, reason = gate_contract_names(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Passed: {passed}")
    if reason:
        print(f"Reason: {reason}")
    sys.exit(0 if passed else 1)
