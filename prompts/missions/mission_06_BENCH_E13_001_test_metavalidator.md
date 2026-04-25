# MISSION: Test Suite Metavalidator
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E13_001_test_metavalidator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Two epochs in a row, the factory was blocked for hours by stale test files
in `06_BENCHMARKING/tests/<domain>/` whose imports pointed to modules that
no longer exist. Each blockage forced a forensic dive to identify the
specific dead import.

This mission builds a metavalidator: a tool that validates the test suite
itself against the current module map of the repository. It runs as part
of pre-flight checks. If any test file imports a module that cannot be
resolved, the metavalidator reports it before the factory wastes 27B-tier
inference cycles on impossible work.

## EXACT IMPORTS:
```python
import ast
import sys
import importlib.util
import json
from pathlib import Path
from typing import List, Dict, Optional
```

## INTERFACE CONTRACT
The deliverable is a script `scripts/test_metavalidator.py` that exposes
two callable functions and a CLI entry point:

### Function 1: scan_test_imports(tests_root: Path) -> List[Dict]
Walks the tests_root directory, parses every `test_*.py` file with the
`ast` module, extracts all import statements, and returns a list of dicts
with the schema:

```
{
    "test_file": str,           # relative path from tests_root
    "imports": List[str],       # top-level module names imported
    "unresolvable": List[str],  # modules that cannot be found
    "is_stale": bool,           # True if any unresolvable imports exist
}
```

A module is considered resolvable if any of these are true:
- It is in the Python standard library
- It exists as a top-level package in the repo (has `__init__.py`)
- `importlib.util.find_spec()` can locate it

### Function 2: archive_stale_tests(tests_root: Path, graveyard: Path) -> int
Calls scan_test_imports, finds all stale test files, moves them to the
graveyard directory (creating it if needed), and returns the count of
archived files. Must be idempotent — re-running on a clean tree archives
zero files without error.

### CLI Entry Point
When invoked with `python3 scripts/test_metavalidator.py [scan|archive]`:
- `scan` prints a JSON report of all stale tests to stdout, exits 0 if
  none found, exits 1 if any found
- `archive` performs the archiving operation and prints a summary

## DELIVERABLE
File: scripts/test_metavalidator.py

## BEHAVIORAL REQUIREMENTS
- Deterministic: same input tree always produces same output
- Idempotent: safe to run repeatedly
- Read-only by default: must require explicit `archive` command to move files
- Zero false positives: must not flag tests whose imports successfully resolve
- Reports must be JSON-serializable

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. scan_test_imports correctly identifies stale imports in a fixture tree
2. scan_test_imports returns empty unresolvable list for valid tests
3. archive_stale_tests is idempotent (second run archives zero files)
4. CLI scan exits 0 when clean, 1 when stale tests present
5. CLI archive moves files to the graveyard and reports count

## CONSTRAINTS
- No external dependencies beyond stdlib
- Must handle malformed Python files gracefully (catch SyntaxError)
- Must not import the test files themselves (parse only)
- Output valid Python only
