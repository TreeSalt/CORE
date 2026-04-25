# MISSION: Repo Archivist — Move Stale Files to Archive
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E12_001_repo_archivist
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import shutil
import os
from pathlib import Path
```

## CONTEXT
Over 11 epochs, stale artifacts have accumulated in the repo. This script
identifies and safely moves them to an archive directory.

## REQUIREMENTS
Write `scripts/repo_archivist.py` with a function `archive_stale()` that:

1. Defines REPO_ROOT as the parent of the script's directory
2. Creates an `archive/` directory at REPO_ROOT if it does not exist
3. Moves all .py files from `06_BENCHMARKING/tests/_misplaced/` into archive
4. Moves all .md files from `prompts/missions/PENDING/` into archive
5. Moves `state/mission_queue_v9_9_83.json` into archive if it exists
6. Prints how many files were moved
7. Skips any source path that does not exist

The script should be runnable with `python3 scripts/repo_archivist.py`.

## DELIVERABLE
File: scripts/repo_archivist.py

## CONSTRAINTS
- Use shutil.move() — never delete files
- Idempotent: safe to run multiple times
- Output valid Python only
