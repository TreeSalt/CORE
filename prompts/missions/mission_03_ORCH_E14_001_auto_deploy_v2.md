# MISSION: auto_deploy_v2 — Fix Cross-Contamination Bug
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E14_001_auto_deploy_v2
TYPE: IMPLEMENTATION
VERSION: 2.0
MISSION_ID: 03_ORCH_E14_001_auto_deploy_v2

## CONTEXT
The current `scripts/auto_deploy.py` matches proposals to missions by
`PROPOSALS_DIR.glob(f"PROPOSAL_{domain}_*.md")` sorted by mtime. When
multiple ratified missions share a domain, the latest proposal in the
domain gets written to ALL their deliverable paths. The forensic hash
of the bug is `7e20f927b7f041073b9de0824ec53e1f8fdb22e8c10682e776a7a62a3895718a`.

This mission replaces auto_deploy.py with mission_id-based matching,
adds a forensic hash refusal check, and adds explicit logging.

## EXACT IMPORTS
```python
import re
import json
import hashlib
import logging
import py_compile
from pathlib import Path
from typing import Optional
```

## INTERFACE CONTRACT
Deliverable: `scripts/auto_deploy.py`

### Module-level constants
- `REPO_ROOT` (Path), `PROPOSALS_DIR` (Path), `MISSIONS_DIR` (Path)
- `KNOWN_BUG_HASHES` (set[str]) initialized with the forensic hash above
- `log` (Logger)

### Function: extract_code_blocks(proposal_path: Path) -> list[str]
Return list of stripped Python code blocks from markdown fences.

### Function: find_best_block(blocks: list[str]) -> Optional[str]
Return longest syntactically valid block via compile(). None if none compile.

### Function: extract_mission_id_from_proposal(proposal_path: Path) -> Optional[str]
Parse proposal frontmatter for `MISSION_ID:` field. Returns None if absent.

### Function: find_deliverable_path(proposal_path: Path, mission_file: Optional[str]) -> Optional[str]
Check proposal File: directives first, fall back to mission file File: line.

### Function: deploy_proposal(proposal_path: Path, mission: dict) -> dict
Returns dict with keys: status, path, lines, reason, mission_id_match.

CRITICAL behaviors:
1. Compute SHA256 of extracted code BEFORE writing
2. Refuse if hash is in KNOWN_BUG_HASHES — return status="REFUSED_KNOWN_BUG"
3. If proposal has MISSION_ID field, verify it matches mission["id"]
4. If mismatch: return status="REFUSED_MISSION_ID_MISMATCH"
5. If target.exists() and existing hash != new hash: log diff and skip
6. Pre-write syntax check via compile()
7. Write file, re-read, verify post-write hash matches expected

### Function: deploy_all_ratified(queue_path: Optional[Path] = None) -> list[dict]
For each RATIFIED mission:
1. Get mission's domain and id
2. Find proposals matching the domain
3. Parse each proposal's mission_id field
4. Match by mission_id when possible, fall back to mtime with WARN log
5. Call deploy_proposal with the matched proposal
6. Return list of result dicts

## BEHAVIORAL REQUIREMENTS
- Pre-deployment hash check is MANDATORY
- Every refusal logged with full forensic detail
- Idempotent: safe to run repeatedly
- Must work with both new (mission_id-tagged) and legacy proposals

## CONSTRAINTS
- Pure stdlib only
- Python 3.10+
- Must NOT import from mantis_core
- Output valid Python only
