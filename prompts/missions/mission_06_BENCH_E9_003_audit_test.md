# MISSION: Deployment Audit Test Suite

Write a test file: 06_BENCHMARKING/tests/05_REPORTING/test_deployment_audit.py

Write these tests:

1. test_get_proposals_returns_list: verify get_all_proposals returns a list of dicts
2. test_deployed_files_excludes_init: verify __init__.py not in results
3. test_missing_deployments_found: create mock proposals and deployed list, verify gap detected
4. test_report_generates_markdown: verify generate_report creates a .md file

Use pytest and tempfile. No external packages beyond pytest.
