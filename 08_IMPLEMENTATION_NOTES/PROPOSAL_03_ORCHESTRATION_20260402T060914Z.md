---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

class RepoArchivist:
    def __init__(self):
        self.base_archive = Path("archive")
        self.manifest_path = self.base_archive / "ARCHIVE_MANIFEST.json"
        self.move_log = []
        
    def _ensure_archive(self):
        """Creates archive directory tree if needed."""
        self.base_archive.mkdir(parents=True, exist_ok=True)
        
    def _get_timestamp(self):
        """Returns current timestamp in UTC."""
        return datetime.now(timezone.utc).isoformat()
    
    def _log_move(self, source, dest, reason):
        """Logs a move operation to manifest."""
        entry = {
            "timestamp": self._get_timestamp(),
            "source": str(source),
            "destination": str(dest),
            "reason": reason,
            "size": os.path.getsize(source) if source.exists() else 0
        }
        self.move_log.append(entry)
    
    def _write_manifest(self):
        """Writes manifest log to JSON file."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.move_log, f, indent=2)
            
    def move_misplaced_tests(self):
        """Moves misplaced test files to archive."""
        source = Path("06_BENCHMARKING/tests/_misplaced/*.py")
        dest = self.base_archive / "misplaced_tests"
        
        if not source.exists():
            return 0, 0
            
        dest.mkdir(parents=True, exist_ok=True)
        files_moved = 0
        bytes_reclaimed = 0
        
        for file_path in source.glob("*"):
            filename = file_path.name
            target = dest / filename
            
            if not target.exists():
                shutil.move(str(file_path), str(target))
                files_moved += 1
                bytes_reclaimed += file_path.stat().st_size
                self._log_move(file_path, target, "Misplaced test artifact")
                
        return files_moved, bytes_reclaimed
        
    def move_pending_prompts(self):
        """Moves pending prompt files to archive."""
        source = Path("prompts/missions/PENDING/*")
        dest = self.base_archive / "stale_pending"
        
        if not source.exists():
            return 0, 0
            
        dest.mkdir(parents=True, exist_ok=True)
        files_moved = 0
        bytes_reclaimed = 0
        
        for file_path in source.glob("*"):
            target = dest / file_path.name
            
            if not target.exists():
                shutil.move(str(file_path), str(target))
                files_moved += 1
                bytes_reclaimed += file_path.stat().st_size
                self._log_move(file_path, target, "Stale pending prompt")
                
        return files_moved, bytes_reclaimed
        
    def move_mission_queue(self):
        """Moves mission queue JSON to archive."""
        source = Path("state/mission_queue_v9_9_83.json")
        dest = self.base_archive / "mission_queue_v9_9_83.json"
        
        if not source.exists():
            return 0, 0
            
        self._ensure_archive()
        target = self.base_archive / source.name
        
        if not target.exists():
            shutil.move(str(source), str(target))
            files_moved = 1
            bytes_reclaimed = source.stat().st_size
            self._log_move(source, target, "Mission queue state file")
            
            return files_moved, bytes_reclaimed
            
        return 0, 0
        
    def move_empty_drop_files(self):
        """Moves empty TRADER_OPS_COUNCIL_DROP files to archive."""
        source = Path("prompts/missions/TRADER_OPS_COUNCIL_DROP_v4.7.*.txt")
        dest = self.base_archive / "empty_drops"
        
        if not source.exists():
            return 0, 0
            
        dest.mkdir(parents=True, exist_ok=True)
        files_moved = 0
        bytes_reclaimed = 0
        
        for file_path in source.glob("*"):
            # Check if file is empty
            if file_path.stat().st_size == 0:
                target = dest / file_path.name
                
                if not target.exists():
                    shutil.move(str(file_path), str(target))
                    files_moved += 1
                    bytes_reclaimed += 0  # Empty file has no size
                    self._log_move(file_path, target, "Empty TRADER_OPS_COUNCIL_DROP artifact")
                    
        return files_moved, bytes_reclaimed
        
    def archive(self):
        """Main archiving routine that executes all move operations."""
        self._ensure_archive()
        
        total_files = 0
        total_bytes = 0
        
        # Execute each archiving task in order
        f, b = self.move_misplaced_tests()
        total_files += f
        total_bytes += b
        
        f, b = self.move_pending_prompts()
        total_files += f
        total_bytes += b
        
        f, b = self.move_mission_queue()
        total_files += f
        total_bytes += b
        
        f, b = self.move_empty_drop_files()
        total_files += f
        total_bytes += b
        
        # Write manifest before returning summary
        self._write_manifest()
        
        return total_files, total_bytes


def main():
    archivist = RepoArchivist()
    
    files_archived, bytes_reclaimed = archivist.archive()
    
    print(f"Summary: {files_archived} files archived, {bytes_reclaimed} bytes reclaimed")


if __name__ == "__main__":
    import os
    main()