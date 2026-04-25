# MISSION: MIN_SUBSTANCE_GATE — Reject Empty Proposals
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E14_001_min_substance_gate
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E14_001_min_substance_gate

## CONTEXT
PROPOSAL_08_CYBERSECURITY_20260409T040929Z.md contained zero lines of
code (only YAML frontmatter) yet scored 1.0 on the benchmark and was
ratified. See `state/sovereign_vault/e14_backlog/E14_BACKLOG_004_empty_proposal_benchmark_pass.json`.

This mission implements a benchmark gate that rejects proposals failing
minimum substance thresholds.

## EXACT IMPORTS
```python
import re
import ast
from pathlib import Path
from dataclasses import dataclass
```

## INTERFACE CONTRACT
Deliverable: `06_BENCHMARKING/gates/min_substance.py`

### Constants
- `MIN_FILE_BYTES = 500`
- `MIN_CODE_LINES = 20`
- `MIN_FUNCTION_DEFS = 1`

### Dataclass: SubstanceCheckResult (frozen)
Fields: passed (bool), file_bytes (int), code_lines (int),
function_defs (int), class_defs (int), reason (str)

### Function: check_proposal_substance(proposal_path: Path) -> SubstanceCheckResult
1. Read file bytes — fail if under MIN_FILE_BYTES
2. Extract Python blocks via regex `r'```(?:python)?\s*\n(.*?)```'`
3. Use ast.parse to count function and class definitions in largest valid block
4. Count non-blank, non-comment code lines
5. Return SubstanceCheckResult populated

### Function: gate_min_substance(proposal_path: Path) -> tuple[bool, str]
Wrapper returning (passed, human_readable_reason).

## CONSTRAINTS
- Pure stdlib (ast, re, dataclasses, pathlib)
- No imports from mantis_core
- Must handle malformed markdown gracefully
- Must handle proposals with no code blocks (returns passed=False)
