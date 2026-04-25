# MISSION: core queue reset-escalated CLI Command

Write a Python module: scripts/reset_escalated.py

This script resets all ESCALATE missions back to PENDING status.

Write these functions:

1. reset_escalated(queue_path) -> list
   - Reads MISSION_QUEUE.json
   - Finds all missions with status "ESCALATE"
   - Changes their status to "PENDING" and clears started_at
   - Returns list of reset mission IDs

2. reset_by_domain(queue_path, domain_id) -> list
   - Same but only resets missions matching the given domain

Add CLI: python3 scripts/reset_escalated.py [--domain X]
Use only json, pathlib, sys. No external packages.
