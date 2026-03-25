# MISSION: core deploy Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/03_ORCHESTRATION/test_core_deploy.py

## REQUIREMENTS
- test_extract_code_from_proposal: create temp markdown with code block, verify extraction
- test_extract_deliverable_path: verify File: line parsing in multiple formats
- test_dry_run_does_not_write: verify dry run returns info without creating files
- test_syntax_check_catches_errors: verify invalid Python is rejected before writing
- Use pytest and tempfile
- No external calls
- Output valid Python only
