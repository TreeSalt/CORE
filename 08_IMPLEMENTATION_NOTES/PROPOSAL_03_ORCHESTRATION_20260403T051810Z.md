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
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    
    sources = []
    
    misplaced_dir = REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced"
    if misplaced_dir.exists():
        for f in misplaced_dir.iterdir():
            if f.is_file() and f.suffix == ".py":
                sources.append(f)
                
    pending_dir = REPO_ROOT / "prompts" / "missions" / "PENDING"
    if pending_dir.exists():
        for f in pending_dir.iterdir():
            if f.is_file() and f.suffix == ".md":
                sources.append(f)
                
    json_path = REPO_ROOT / "state" / "mission_queue_v9_9_83.json"
    if json_path.exists():
        sources.append(json_path)
        
    count = 0
    for src in sources:
        if src.exists():
            shutil.move(str(src), str(ARCHIVE / src.name))
            count += 1
            
    print(count)

if __name__ == "__main__":
    archive_stale()