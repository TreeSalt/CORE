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
        ARCHIVE.mkdir(parents=True)
        
    src_paths = []
    
    misplaced_dir = REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced"
    if misplaced_dir.exists():
        src_paths.extend(list(misplaced_dir.glob("*.py")))
        
    pending_dir = REPO_ROOT / "prompts" / "missions" / "PENDING"
    if pending_dir.exists():
        src_paths.extend(list(pending_dir.glob("*.md")))
        
    queue_file = REPO_ROOT / "state" / "mission_queue_v9_9_83.json"
    if queue_file.exists():
        src_paths.append(queue_file)
    
    count = 0
    for src in src_paths:
        if src.exists():
            dest = ARCHIVE / src.name
            shutil.move(str(src), str(dest))
            count += 1
            
    print(count)

if __name__ == "__main__":
    archive_stale()