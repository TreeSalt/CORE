# MISSION: Proposal Code Extractor

Write a Python module: scripts/proposal_extractor.py

This module extracts Python code from ratified proposal markdown files.

Write these functions:

1. extract_code_blocks(proposal_path) -> list of str
   - Reads a proposal markdown file
   - Extracts all python code blocks (between ```python and ```)
   - Returns list of code strings

2. find_best_block(blocks) -> str or None
   - Takes list of code blocks
   - Returns the longest one that compiles without SyntaxError
   - Returns None if no valid blocks found

3. find_deliverable_path(proposal_path, mission_dir) -> str or None
   - Checks the proposal for File: lines in any format
   - If not found, checks the corresponding mission file
   - Returns the deliverable path or None

4. deploy_proposal(proposal_path, mission_dir, dry_run) -> dict
   - Extracts code, finds deliverable path, writes file
   - Returns {"status": "OK"|"ERROR", "path": str, "lines": int}

CLI: python3 scripts/proposal_extractor.py PROPOSAL.md [--dry-run]
Use only re, pathlib, sys, py_compile. No external packages.
