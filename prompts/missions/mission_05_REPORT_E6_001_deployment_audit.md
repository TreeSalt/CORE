# MISSION: Deployment Audit Report

Write a Python module: scripts/deployment_audit.py

This module audits the gap between ratified proposals and deployed files.

Write these functions:

1. get_all_proposals(notes_dir) -> list of dict
   - Scans 08_IMPLEMENTATION_NOTES for PROPOSAL_*.md files
   - For each, extracts: domain, timestamp, has_code_block (bool), deliverable_path (str or None)

2. get_deployed_files(repo_root) -> list of str
   - Walks domain directories and scripts/redteam
   - Returns list of deployed .py file paths (not __init__.py)

3. find_missing_deployments(proposals, deployed) -> list of dict
   - Compares proposals with deliverable paths against deployed files
   - Returns list of proposals whose deliverable is NOT on disk

4. generate_report(missing, output_path) -> None
   - Writes a markdown report listing every undeployed proposal
   - Groups by domain, sorted by timestamp

CLI: python3 scripts/deployment_audit.py
Use only pathlib, re, json. No external packages.
