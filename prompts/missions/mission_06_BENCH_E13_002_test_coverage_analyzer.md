# MISSION: Test Coverage Analyzer — Gap Identification Tool
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E13_002_test_coverage_analyzer
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The repository has 348 Python files but only 52 test files (~15% coverage
by file count). More importantly, recently deployed E12 modules like
trade_journal.py, regime_performance.py, dual_lane_orchestrator.py,
and cgroup_manager.py have no corresponding test files at all. The
benchmark logic gate auto-passes for these because no tests exist —
which masks the absence of validation.

This mission builds a coverage analyzer that identifies which deliverables
have no tests, scans each untested module to extract its public interface
(classes, methods, functions), and produces a structured gap report. The
report serves as input for follow-up test-writing missions.

The analyzer does not generate tests itself — that violates the "no
spoon-feeding" principle. It produces a structured catalog of what tests
SHOULD exist so the factory can plan future missions.

## EXACT IMPORTS:
```python
import ast
import json
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set
```

## INTERFACE CONTRACT
The deliverable is `scripts/test_coverage_analyzer.py` containing both an
importable API and a CLI entry point.

### Dataclass: PublicSymbol
Frozen dataclass with these fields:
```
name: str                   # symbol name (class or function)
kind: str                   # one of "class", "function", "method"
parent: Optional[str]       # parent class name if kind is "method"
line_number: int
docstring: Optional[str]
parameters: List[str]       # parameter names (excluding self)
```

### Dataclass: ModuleAnalysis
Frozen dataclass with these fields:
```
module_path: str            # relative to repo root
public_symbols: List[PublicSymbol]
has_test_file: bool
expected_test_path: str     # where the test file should live
total_lines: int
```

### Dataclass: CoverageGapReport
Frozen dataclass with these fields:
```
generated_at: str           # ISO UTC
total_modules: int
modules_with_tests: int
modules_without_tests: int
coverage_pct: float         # percentage with tests
untested_modules: List[ModuleAnalysis]
critical_gaps: List[str]    # names of high-priority untested modules
```

### Function: extract_public_symbols(file_path: Path) -> List[PublicSymbol]
Parses a Python file with the ast module and extracts all top-level
classes and functions, plus methods within classes. A symbol is considered
public if its name does NOT start with an underscore. Returns the list
of PublicSymbol records. Returns empty list if file has SyntaxError.

### Function: find_test_file(module_path: Path, src_root: Path, tests_root: Path) -> Optional[Path]
Given a source module path, returns the expected test file path. The
convention is:
- Source: `mantis_core/risk/trade_journal.py`
- Test:   `06_BENCHMARKING/tests/02_RISK_MANAGEMENT/test_trade_journal.py`
The function looks for the test file at the expected location and returns
the path if it exists, None otherwise. Domain mapping (e.g., "risk" ->
"02_RISK_MANAGEMENT") must be configurable via a constant DOMAIN_MAP.

### Function: analyze_module(module_path: Path, src_root: Path, tests_root: Path) -> ModuleAnalysis
Combines extract_public_symbols and find_test_file. Returns a populated
ModuleAnalysis dataclass.

### Function: scan_repository(src_dirs: List[Path], tests_root: Path) -> List[ModuleAnalysis]
Walks all src_dirs recursively, finds all .py files, excludes __init__.py
and conftest.py, calls analyze_module on each, returns the full list.

### Function: identify_critical_gaps(analyses: List[ModuleAnalysis]) -> List[str]
Returns names of untested modules that meet ANY of these criteria:
- Module is in mantis_core/risk/ (financial safety critical)
- Module is in mantis_core/orchestration/ (system stability critical)
- Module has 5 or more public symbols (large surface area)
- Module name contains "deploy", "execute", "trade", or "auto"

### Function: generate_report(analyses: List[ModuleAnalysis]) -> CoverageGapReport
Aggregates all analyses into a CoverageGapReport. Sorts untested modules
by line count descending (largest gaps first). Calls identify_critical_gaps.

### CLI Entry Point
When invoked with `python3 scripts/test_coverage_analyzer.py [report|critical] [--output PATH]`:
- `report` produces the full CoverageGapReport as JSON
- `critical` produces only the critical_gaps list as a plain text list
- `--output` writes to file instead of stdout
- `--src-dirs` defaults to "mantis_core,scripts"
- `--tests-root` defaults to "06_BENCHMARKING/tests"

Exit codes: 0 if coverage_pct >= 80, 1 if below 80.

## DELIVERABLE
File: scripts/test_coverage_analyzer.py

## BEHAVIORAL REQUIREMENTS
- Read-only — never modifies any source or test files
- Deterministic given the same input tree
- Handles SyntaxError gracefully (skips file, logs warning)
- Excludes auto-generated files and __init__.py
- All timestamps timezone-aware UTC, ISO format
- Output valid JSON when in JSON mode

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. extract_public_symbols correctly identifies classes, functions, methods
2. extract_public_symbols excludes underscore-prefixed names
3. extract_public_symbols handles SyntaxError gracefully
4. find_test_file returns correct path based on domain mapping
5. analyze_module integrates symbol extraction and test detection
6. identify_critical_gaps flags modules in risk/ and orchestration/
7. generate_report sorts by line count descending
8. CLI report command produces valid JSON
9. CLI exit code is 1 when coverage below 80%

## CONSTRAINTS
- Pure stdlib only
- No code generation (read-only analysis)
- No file modifications
- Output valid Python only
