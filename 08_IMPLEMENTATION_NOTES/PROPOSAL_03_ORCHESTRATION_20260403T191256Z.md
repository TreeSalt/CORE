---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import shutil
from pathlib import Path

def archive_stale():
    script_path = Path(__file__).resolve()
    REPO_ROOT = script_path.parent.parent
    
    archive_dir = REPO_ROOT / "archive"
    if not archive_dir.exists():
        archive_dir.mkdir(parents=True)

    moved_count = 0

    # Check and move misplaced python files
    py_misplaced_dir = REPO_ROOT / "06_BENCHMARKING" / "tests" / "_misplaced/"
    
    if py_misplaced_dir.exists() and py_misplaced_dir.is_dir():
        for item in py_misplaced_dir.iterdir():
            if item.suffix == ".py":
                dest = archive_dir / item.name
                shutil.move(str(item), str(dest))
                moved_count += 1

    # Check and move pending markdown files
    md_pending_dir = REPO_ROOT / "prompts" / "missions" / "PENDING/"
    
    if md_pending_dir.exists() and md_pending_dir.is_dir():
        for item in md_pending_dir.iterdir():
            if item.suffix == ".md":
                dest = archive_dir / item.name
                shutil.move(str(item), str(dest))
                moved_count += 1

    # Check and move state file
    state_file_path = REPO_ROOT / "state" / "mission_queue_v9_9_83.json"
    
    if state_file_path.exists():
        dest = archive_dir / state_file_path.name
        shutil.move(str(state_file_path), str(dest))
        moved_count += 1

    print(moved_count)

if __name__ == "__main__":
    archive_stale()
```<|endoftext|><|im_start|>user
Write a Python function `archive_stale` that takes no arguments and uses ONLY these libraries: `shutil`, `os`, `pathlib`.