# MISSION: IMPORT_RESOLUTION_GATE — Catch Hallucinated Imports
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E14_002_import_resolution_gate

## CONTEXT
preflight_runner (E13.P14) imported `from manticore.core.modules.doctor
import AgentEntry as DoctorAgent` — entirely fabricated. The package
does not exist. The benchmark gate accepted the syntactically valid
proposal. See `state/sovereign_vault/e14_backlog/E14_BACKLOG_002_preflight_runner_v5.json`.

## EXACT IMPORTS
```python
import ast
import sys
import importlib.util
from pathlib import Path
```

## INTERFACE CONTRACT
Deliverable: `06_BENCHMARKING/gates/import_resolution.py`

### Function: extract_imports_from_code(code: str) -> list[str]
Walk Import and ImportFrom AST nodes. Return list of top-level module
names (e.g., 'mantis_core.orchestration', 'json').

### Function: is_stdlib_module(module_name: str) -> bool
Return True if module is in `sys.stdlib_module_names`.

### Function: can_resolve_module(module_name: str, repo_root: Path) -> bool
Try importlib.util.find_spec on the top-level package name. Also check
if module exists as a file path under repo_root.

### Function: gate_import_resolution(proposal_path: Path, repo_root: Path) -> tuple[bool, str]
Extract imports from largest valid block. For each non-stdlib import,
attempt resolution. Return (False, reason) if any unresolvable, else (True, "").

## SECURITY CRITICAL
- Must NOT actually execute the imports
- importlib.util.find_spec is safe — does not execute modules
- Handle relative imports (from . import x) — return True for these

## CONSTRAINTS
- Pure stdlib (ast, importlib, sys, pathlib)
