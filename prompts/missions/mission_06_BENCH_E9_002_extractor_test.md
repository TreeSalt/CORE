# MISSION: Proposal Extractor Test Suite

Write a test file: 06_BENCHMARKING/tests/03_ORCHESTRATION/test_proposal_extractor.py

Write these tests:

1. test_extract_code_blocks: create temp markdown with python code block, verify extraction
2. test_find_best_block_picks_longest_valid: provide 3 blocks (1 invalid, 2 valid), verify longest valid returned
3. test_find_deliverable_from_proposal: verify File: line parsing works
4. test_dry_run_no_write: verify deploy with dry_run does not create files

Use pytest and tempfile. No external packages beyond pytest.
