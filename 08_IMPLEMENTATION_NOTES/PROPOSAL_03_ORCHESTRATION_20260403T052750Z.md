---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import shutil
import json
import os
from pathlib import Path
from datetime import datetime, timezone


def archive_stale():
    REPO_ROOT = Path(__file__).resolve().parents[1]
    ARCHIVE = REPO_ROOT / "archive"

    if not ARCHIVE.exists():
        ARCHIVE.mkdir(parents=True, exist_ok=True)

    source_paths = []

    # 1. All .py files in REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced"
    src_dir_1 = REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced"
    if src_dir_1.exists():
        source_paths.extend(src_dir_1.glob("*.py"))

    # 2. All .md files in REPO_ROOT / "prompts" / "missions" / "PENDING"
    src_dir_2 = REPO_ROOT / "prompts" / "missions" / "PENDING"
    if src_dir_2.exists():
        source_paths.extend(src_dir_2.glob("*.md"))

    # 3. REPO_ROOT / "state" / "mission_queue_v9_9_83.json" (if exists)
    specific_file = REPO_ROOT / "state" / "mission_queue_v9_9_83.json"
    if specific_file.exists():
        source_paths.append(specific_file)

    moved_count = 0

    for src in source_paths:
        if src.exists():
            dst = ARCHIVE / src.name
            shutil.move(str(src), str(dst))
            moved_count += 1

    print(moved_count)


if __name__ == "__main__":
    archive_stale()