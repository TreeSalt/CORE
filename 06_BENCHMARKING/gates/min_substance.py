#!/usr/bin/env python3
"""
MIN_SUBSTANCE_GATE — Reject Empty/Trivial Proposals
=====================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection (factory cannot self-validate)

PURPOSE
Catches the failure mode documented in E14_BACKLOG_004:
PROPOSAL_08_CYBERSECURITY_20260409T040929Z.md contained zero lines of
code (only YAML frontmatter) yet scored 1.0 on the benchmark and was
ratified. Empty proposals trivially pass tests because there is nothing
to fail.

This gate runs BEFORE benchmark scoring. A proposal that fails substance
checks gets rejected immediately — no benchmark score is computed,
no ratification path is opened, the failure becomes a first-class event.

INTEGRATION POINT
The benchmark runner should call gate_min_substance(proposal_path) as
the first step in its pipeline. If it returns (False, reason), the
runner emits a SUBSTANCE_GATE_FAILURE escalation and skips scoring.

THRESHOLDS
- MIN_FILE_BYTES: 500 (catches frontmatter-only proposals)
- MIN_CODE_LINES: 20 (catches stub-only proposals)
- MIN_FUNCTION_DEFS: 1 (catches proposals with no callable surface)

These thresholds are deliberately permissive. They only catch the
egregious failures, not borderline cases. Tightening them is a future
calibration exercise once we have data on observed failure modes.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

# Module-level constants (constitutional contract: ALL_CAPS = constants)
MIN_FILE_BYTES = 500
MIN_CODE_LINES = 20
MIN_FUNCTION_DEFS = 1


@dataclass(frozen=True)
class SubstanceCheckResult:
    """Result of a substance check on a proposal file."""
    passed: bool
    file_bytes: int
    code_lines: int
    function_defs: int
    class_defs: int
    reason: str


def _extract_python_blocks(text: str) -> list[str]:
    """Extract all fenced Python code blocks from markdown."""
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def _find_largest_valid_block(blocks: list[str]) -> str | None:
    """Return the longest code block that parses successfully via ast."""
    valid = []
    for block in blocks:
        try:
            ast.parse(block)
            valid.append(block)
        except SyntaxError:
            continue
    return max(valid, key=len) if valid else None


def _count_meaningful_lines(code: str) -> int:
    """Count non-blank, non-comment-only lines."""
    count = 0
    for line in code.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        count += 1
    return count


def _count_module_defs(code: str) -> tuple[int, int]:
    """Return (function_count, class_count) at module level."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return (0, 0)
    funcs = sum(1 for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    classes = sum(1 for n in tree.body if isinstance(n, ast.ClassDef))
    return (funcs, classes)


def check_proposal_substance(proposal_path: Path) -> SubstanceCheckResult:
    """Run all substance checks on a proposal file. Returns full result."""
    if not proposal_path.exists():
        return SubstanceCheckResult(
            passed=False, file_bytes=0, code_lines=0,
            function_defs=0, class_defs=0,
            reason=f"proposal file does not exist: {proposal_path}",
        )

    try:
        text = proposal_path.read_text()
    except Exception as e:
        return SubstanceCheckResult(
            passed=False, file_bytes=0, code_lines=0,
            function_defs=0, class_defs=0,
            reason=f"cannot read proposal: {e}",
        )

    file_bytes = len(text.encode("utf-8"))

    if file_bytes < MIN_FILE_BYTES:
        return SubstanceCheckResult(
            passed=False, file_bytes=file_bytes, code_lines=0,
            function_defs=0, class_defs=0,
            reason=f"file too small: {file_bytes} bytes (min {MIN_FILE_BYTES})",
        )

    blocks = _extract_python_blocks(text)
    if not blocks:
        # Some old-style proposals embed code without fences. Try the raw text.
        if "def " in text or "class " in text:
            code = text
        else:
            return SubstanceCheckResult(
                passed=False, file_bytes=file_bytes, code_lines=0,
                function_defs=0, class_defs=0,
                reason="no python code blocks or definitions found",
            )
    else:
        code = _find_largest_valid_block(blocks)
        if code is None:
            return SubstanceCheckResult(
                passed=False, file_bytes=file_bytes, code_lines=0,
                function_defs=0, class_defs=0,
                reason="no syntactically valid code blocks found",
            )

    code_lines = _count_meaningful_lines(code)
    funcs, classes = _count_module_defs(code)
    total_defs = funcs + classes

    if code_lines < MIN_CODE_LINES:
        return SubstanceCheckResult(
            passed=False, file_bytes=file_bytes, code_lines=code_lines,
            function_defs=funcs, class_defs=classes,
            reason=f"code too short: {code_lines} lines (min {MIN_CODE_LINES})",
        )

    if total_defs < MIN_FUNCTION_DEFS:
        return SubstanceCheckResult(
            passed=False, file_bytes=file_bytes, code_lines=code_lines,
            function_defs=funcs, class_defs=classes,
            reason=f"no function/class definitions found at module level",
        )

    return SubstanceCheckResult(
        passed=True, file_bytes=file_bytes, code_lines=code_lines,
        function_defs=funcs, class_defs=classes,
        reason="",
    )


def gate_min_substance(proposal_path: Path) -> tuple[bool, str]:
    """Wrapper for benchmark runner integration.

    Returns (passed: bool, reason: str). Reason is empty on pass,
    descriptive on fail. The reason text is suitable for direct
    inclusion in escalation messages and ledger entries.
    """
    result = check_proposal_substance(Path(proposal_path))
    if result.passed:
        return (True, "")
    return (False, f"MIN_SUBSTANCE_FAIL: {result.reason}")


# ─── CLI for standalone testing ──────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 min_substance.py <proposal_path>")
        sys.exit(2)
    result = check_proposal_substance(Path(sys.argv[1]))
    print(f"Passed:        {result.passed}")
    print(f"File bytes:    {result.file_bytes}")
    print(f"Code lines:    {result.code_lines}")
    print(f"Function defs: {result.function_defs}")
    print(f"Class defs:    {result.class_defs}")
    if result.reason:
        print(f"Reason:        {result.reason}")
    sys.exit(0 if result.passed else 1)
