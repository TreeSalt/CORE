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
        ARCHIVE.mkdir()
        
    sources = []
    
    misplaced_dir = REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced"
    if misplaced_dir.exists():
        sources.extend(misplaced_dir.glob("*.py"))
        
    pending_dir = REPO_ROOT / "prompts" / "missions" / "PENDING"
    if pending_dir.exists():
        sources.extend(pending_dir.glob("*.md"))
        
    queue_json = REPO_ROOT / "state" / "mission_queue_v9_9_83.json"
    if queue_json.exists():
        sources.append(queue_json)
        
    moved_count = 0
    for src in sources:
        if src.exists():
            dest_path = ARCHIVE / src.name
            shutil.move(str(src), str(dest_path))
            moved_count += 1
            
    print(moved_count)

if __name__ == "__main__":
    archive_stale()<|endoftext|><|im_start|>user
You are a senior Python developer. 
Follow the Blueprint exactly. Write EXACTLY the code described in brief. Output valid Python only. No markdown