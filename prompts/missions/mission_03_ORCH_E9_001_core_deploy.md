# MISSION: core deploy CLI Command
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/core_deploy.py

## REQUIREMENTS
- extract_code_from_proposal(proposal_path) -> str: extract Python code blocks from markdown
- extract_deliverable_path(proposal_path) -> str or None: parse File: line in any format
- deploy(proposal_path, dry_run) -> dict with status, deliverable_path, code_length
- CLI usage: python3 scripts/core_deploy.py path/to/PROPOSAL.md [--dry-run]
- If no File: path found, prompt operator via stdin
- Write extracted code to deliverable path, creating directories as needed
- Run syntax check (py_compile) before writing
- Print diff-style summary of what was written
- No external network calls
- Output valid Python only
