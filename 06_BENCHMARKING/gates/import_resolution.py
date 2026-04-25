#!/usr/bin/env python3
"""
IMPORT_RESOLUTION_GATE — Catch Hallucinated Imports
=====================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection (factory cannot self-validate)

PURPOSE
Catches the failure mode documented in E14_BACKLOG_002:
preflight_runner (E13.P14) imported `from manticore.core.modules.doctor
import AgentEntry as DoctorAgent` — entirely fabricated. The package
does not exist anywhere — not on PyPI, not in the repo, not in stdlib.
The benchmark gate accepted the proposal because the syntax was valid.

This gate statically resolves every import in the proposal's code
against the live repo and the Python stdlib. Any import that cannot
be resolved is treated as a hallucination, the proposal is rejected.

SECURITY CRITICAL
This gate must NEVER execute the imports. It uses importlib.util.find_spec
which only locates modules without running them. Untrusted code is
never executed during validation.

SCOPE
- Stdlib imports: trusted, skipped
- Repo-relative imports (mantis_core.*, scripts.*): resolved against repo
- Third-party imports: resolved against installed packages
- Relative imports (from . import): trusted, skipped
- Conditional/late imports inside functions: NOT checked (intentional —
  many legitimate patterns use try/except ImportError)
"""

import ast
import importlib.util
import sys
from pathlib import Path


def _is_stdlib_module(module_name: str) -> bool:
    """Check if module is part of the Python standard library."""
    if not module_name:
        return False
    top_level = module_name.split(".")[0]
    return top_level in sys.stdlib_module_names


def extract_imports_from_code(code: str) -> list[tuple[str, int]]:
    """Walk AST for top-level Import and ImportFrom nodes.

    Returns list of (module_name, line_number) tuples. Only collects
    imports at the module level — imports inside functions/classes
    are intentionally skipped (they're often conditional/optional).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    imports = []
    # Only walk module-level statements, not function bodies
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            # Skip relative imports (from . import x)
            if node.level > 0:
                continue
            if node.module:
                imports.append((node.module, node.lineno))
    return imports


def can_resolve_module(module_name: str, repo_root: Path) -> bool:
    """Try to resolve a module without executing it.

    Resolution order:
    1. Stdlib check (sys.stdlib_module_names)
    2. importlib.util.find_spec (handles installed packages)
    3. Repo-relative path check (handles project modules even if
       not installed in editable mode)
    """
    if not module_name:
        return False

    # 1. Stdlib
    if _is_stdlib_module(module_name):
        return True

    # 2. importlib spec lookup (does NOT execute the module)
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            return True
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        pass

    # 3. Repo-relative path check
    parts = module_name.split(".")
    candidates = [
        repo_root / Path(*parts) / "__init__.py",
        repo_root / Path(*parts).with_suffix(".py"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return True

    return False


def gate_import_resolution(proposal_path: Path,
                            repo_root: Path | None = None) -> tuple[bool, str]:
    """Wrapper for benchmark runner integration.

    Returns (passed: bool, reason: str). Reason includes the specific
    unresolvable imports if any.
    """
    if repo_root is None:
        repo_root = Path(".").resolve()

    p = Path(proposal_path)
    if not p.exists():
        return (False, "IMPORT_GATE_FAIL: proposal file does not exist")

    try:
        text = p.read_text()
    except Exception as e:
        return (False, f"IMPORT_GATE_FAIL: cannot read proposal: {e}")

    # Extract code blocks (reuse logic from min_substance is fine,
    # but we inline here to keep the gate self-contained)
    import re
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
    blocks = [b.strip() for b in blocks if b.strip()]

    if not blocks:
        return (True, "")  # No code = no imports to check

    # Find the largest valid block
    valid_blocks = []
    for block in blocks:
        try:
            ast.parse(block)
            valid_blocks.append(block)
        except SyntaxError:
            continue

    if not valid_blocks:
        return (True, "")  # No valid code = handled by truncation/syntax gates

    code = max(valid_blocks, key=len)
    imports = extract_imports_from_code(code)

    unresolvable = []
    for module_name, lineno in imports:
        if not can_resolve_module(module_name, repo_root):
            unresolvable.append((module_name, lineno))

    if unresolvable:
        details = ", ".join(f"{m} (line {l})" for m, l in unresolvable[:5])
        if len(unresolvable) > 5:
            details += f" and {len(unresolvable) - 5} more"
        return (False,
                f"IMPORT_GATE_FAIL: unresolvable imports: {details}")

    return (True, "")


# ─── CLI for standalone testing ──────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 import_resolution.py <proposal_path>")
        sys.exit(2)
    passed, reason = gate_import_resolution(Path(sys.argv[1]))
    print(f"Passed: {passed}")
    if reason:
        print(f"Reason: {reason}")
    sys.exit(0 if passed else 1)
