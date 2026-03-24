# MISSION: Periodic Git Commit During Factory Runs
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/periodic_commit.py

## REQUIREMENTS
- should_commit(last_commit_ts, interval_minutes) -> bool
- do_commit(repo_root, message) -> bool: runs git add -A, git commit with message
- get_epoch_summary(queue_path) -> str: generates commit message from queue state
- Designed to be called between missions in the run loop
- All paths are function parameters
- No external network calls
- Output valid Python only
