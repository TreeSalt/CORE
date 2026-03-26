---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

# MISSION: core status CLI Command
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/core_status.py

## REQUIREMENTS
- get_queue_stats(queue_path) -> dict: pending, ratified, escalated, total
- get_deployed_files(repo_root) -> list of deployed python file paths
- get_proposal_stats(notes_dir) -> dict: total, with_code, with_file_path, deployable
- get_deployment_rate(deployed, proposals) -> float percentage
- print_dashboard() -> None: formatted terminal output with all stats
- CLI usage: python3 scripts/core_status.py
- No external network calls
- Output valid Python only