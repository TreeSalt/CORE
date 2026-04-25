---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone


def log_archive_action(source: Path, dest: Path, reason: str, archive_dir: Path) -> None:
    manifest_path = archive_dir / "ARCHIVE_MANIFEST.json"
    action = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "destination": str(dest),
        "reason": reason
    }
    
    if not manifest_path.exists():
        with open(manifest_path, 'w') as f:
            json.dump([action], f, indent=2)
    else:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        manifest.append(action)
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)


def clean_stale_artifacts(archive_base: Path = None):
    if archive_base is None:
        archive_base = Path("archive")
    
    archive_base.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_base / "ARCHIVE_MANIFEST.json"
    
    reclaimed_bytes = 0
    archived_count = 0
    
    # Task 1: Move .py files from misplaced tests to archive/misplaced_tests/
    misplaced_src = Path("06_BENCHMARKING/tests/_misplaced")
    if misplaced_src.exists():
        dest_misplaced = archive_base / "misplaced_tests"
        dest_misplaced.mkdir(parents=True, exist_ok=True)
        
        for py_file in misplaced_src.glob("*.py"):
            if not py_file.exists():
                continue
            
            # Skip if already moved (check destination exists)
            target = dest_misplaced / py_file.name
            if target.exists():
                continue
            
            try:
                shutil.move(str(py_file), str(target))
                log_archive_action(py_file, target, "Stale misplaced test artifact", archive_base)
                reclaimed_bytes += py_file.stat().st_size
                archived_count += 1
            except Exception as e:
                pass
    
    # Task 2: Move files from prompts/missions/PENDING/ to archive/stale_pending/
    pending_src = Path("prompts/missions/PENDING")
    if pending_src.exists():
        dest_pending = archive_base / "stale_pending"
        dest_pending.mkdir(parents=True, exist_ok=True)
        
        for file in pending_src.iterdir():
            if not file.is_file():
                continue
            
            # Skip if already moved (check destination exists)
            target = dest_pending / file.name
            if target.exists():
                continue
            
            try:
                shutil.move(str(file), str(target))
                log_archive_action(file, target, "Stale pending mission prompt", archive_base)
                reclaimed_bytes += file.stat().st_size
                archived_count += 1
            except Exception as e:
                pass
    
    # Task 3: Move state/mission_queue_v9_9_83.json to archive/
    queue_file = Path("state/mission_queue_v9_9_83.json")
    if queue_file.exists():
        target = archive_base / "mission_queue_v9_9_83.json"
        # Skip if already moved (check destination exists)
        if not target.exists():
            try:
                shutil.move(str(queue_file), str(target))
                log_archive_action(queue_file, target, "Queue artifact cleanup", archive_base)
                reclaimed_bytes += queue_file.stat().st_size
                archived_count += 1
            except Exception as e:
                pass
    
    # Task 4: Move empty TRADER_OPS_COUNCIL_DROP files to archive/
    trader_drop_pattern = Path("prompts/missions/TRADER_OPS_COUNCIL_DROP_v4.7.*.txt")
    if trader_drop_pattern.exists():
        dest_trader = archive_base / "trader_ops_drop"
        dest_trader.mkdir(parents=True, exist_ok=True)
        
        for file in trader_drop_pattern.glob("*.txt"):
            if not file.is_file():
                continue
            
            # Check if file is empty (size == 0)
            try:
                if file.stat().st_size > 0:
                    continue
            except FileNotFoundError:
                pass
            
            target = dest_trader / file.name
            if target.exists():
                continue
            
            try:
                shutil.move(str(file), str(target))
                log_archive_action(file, target, "Empty trader ops council drop artifact", archive_base)
                reclaimed_bytes += file.stat().st_size
                archived_count += 1
            except Exception as e:
                pass
    
    print(f"Files archived: {archived_count}")
    print(f"Bytes reclaimed: {reclaimed_bytes}")


if __name__ == "__main__":
    clean_stale_artifacts()
```