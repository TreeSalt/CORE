# MISSION: Fix COUNCIL_CANON.yaml Duplicate Lines
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E12_002_canon_dedup_fix
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
from pathlib import Path
```

## CONTEXT
The build system appends a line to COUNCIL_CANON.yaml on every build instead
of replacing the existing line, creating duplicate entries over time.

## REQUIREMENTS
Write `scripts/fix_canon_dedup.py` with a function `dedup_canon()` that:

1. Reads `docs/ready_to_drop/COUNCIL_CANON.yaml` as raw text lines
2. Removes any exact duplicate lines while preserving order (keep first occurrence)
3. Writes the deduplicated content back to the same file
4. Prints how many duplicate lines were removed

The script should be runnable with `python3 scripts/fix_canon_dedup.py`.

## DELIVERABLE
File: scripts/fix_canon_dedup.py

## CONSTRAINTS
- Preserve all unique content in original order
- Idempotent: safe to run multiple times
- Output valid Python only
