# MISSION: core prompt Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/03_ORCHESTRATION/test_core_prompt.py

## REQUIREMENTS
- test_generate_mission_file: verify generated mission markdown has required sections
- test_validate_clean_mission: verify clean mission returns no issues
- test_queue_mission_appends: verify mission is appended to queue JSON
- test_all_domains_accepted: verify all 9 domain IDs are accepted
- Use pytest and tempfile
- No external calls
- Output valid Python only
