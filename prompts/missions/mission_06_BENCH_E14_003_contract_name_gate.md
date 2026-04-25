# MISSION: CONTRACT_NAME_GATE — Enforce Brief Contracts
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E14_003_contract_name_gate

## CONTEXT
Both tier_loader_v4 and preflight_runner exhibited FUNCTION_NAME_DRIFT.
The model wrote functions named differently than the brief specified
(verify_doctor_module instead of check_doctor). See E14 backlog 001 and 002.

## EXACT IMPORTS
```python
import ast
import re
from pathlib import Path
```

## INTERFACE CONTRACT
Deliverable: `06_BENCHMARKING/gates/contract_name.py`

### Function: extract_contract_names_from_brief(brief_text: str) -> dict
Parse brief markdown for INTERFACE CONTRACT section. Find:
- Lines starting with "### Function:" — extract function name
- Lines starting with "### Dataclass:" — extract class name
- Lines starting with "### Class:" — extract class name
- Constants section: lines matching `^- ([A-Z_]+)\s*=`

Return: {"functions": [...], "classes": [...], "constants": [...]}

### Function: extract_defined_names_from_code(code: str) -> dict
Walk AST. Return same dict structure with names defined in proposal.
- functions: FunctionDef and AsyncFunctionDef at module level
- classes: ClassDef at module level
- constants: Assign targets at module level where name is ALL_CAPS

### Function: gate_contract_names(brief_path: Path, proposal_path: Path) -> tuple[bool, str]
For each contract name, verify exact match in defined names.
Return (False, list of missing names) or (True, "").

## BEHAVIORAL
- Exact match only — no fuzzy or substring matching
- If brief has no INTERFACE CONTRACT section, return (True, "no contract")
  (legacy briefs are exempt)

## CONSTRAINTS
- Pure stdlib (ast, re, pathlib)
