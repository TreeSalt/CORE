---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import shutil
import os
from pathlib import Path

def archive_stale():
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    archive_dir = repo_root / "archive"
    
    # Create archive directory if it doesn't exist
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    files_moved = 0
    
    # Move .py files from 06_BENCHMARKING/tests/_misplaced/
    misplaced_path = repo_root / "06_BENCHMARKING" / "tests" / "_misplaced"
    if misplaced_path.exists():
        for py_file in misplaced_path.glob("*.py"):
            shutil.move(str(py_file), str(archive_dir / py_file.name))
            files_moved += 1
    
    # Move .md files from prompts/missions/PENDING/
    pending_path = repo_root / "prompts" / "missions" / "PENDING"
    if pending_path.exists():
        for md_file in pending_path.glob("*.md"):
            shutil.move(str(md_file), str(archive_dir / md_file.name))
            files_moved += 1
    
    # Move mission queue JSON if it exists
    queue_file = repo_root / "state" / "mission_queue_v9_9_83.json"
    if queue_file.exists():
        shutil.move(str(queue_file), str(archive_dir / queue_file.name))
        files_moved += 1
    
    print(f"Files moved: {files_moved}")

if __name__ == "__main__":
    archive_stale()