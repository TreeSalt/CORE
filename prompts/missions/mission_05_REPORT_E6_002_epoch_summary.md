# MISSION: Epoch Summary Generator

Write a Python module: scripts/epoch_summary.py

This module generates a summary of the current epoch results.

Write these functions:

1. load_queue(queue_path) -> dict
   - Reads MISSION_QUEUE.json and returns parsed data

2. compute_stats(queue) -> dict
   - Returns: total, ratified, escalated, pending, pass_rate, domains breakdown

3. generate_markdown(stats, output_path) -> None
   - Writes a formatted markdown report with epoch results
   - Includes domain-by-domain breakdown
   - Includes list of escalated missions with their IDs

4. generate_commit_message(stats) -> str
   - Returns a formatted git commit message summarizing the epoch

CLI: python3 scripts/epoch_summary.py [--output path]
Use only json, pathlib, sys. No external packages.
