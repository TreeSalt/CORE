# MISSION: Test Suite — Bounty Engine Modules
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E11_003_bounty_test
TYPE: TEST
VERSION: 1.1

## CONTEXT
Tests for the E11 bounty engine modules in mantis_core.

## EXACT IMPORTS (use these, not any other paths):
```python
from mantis_core.security.target_scraper import TargetScraper, BountyTarget
from mantis_core.security.recon_engine import ReconEngine, ReconProfile
from mantis_core.security.submission_tracker import SubmissionTracker, Submission
```

## BLUEPRINT
TestTargetScraper: dataclass creation, dedup, AI filter, graceful offline,
rate limit (5 tests)

TestReconEngine: profile created, scope respected, requests logged, risk score
range, prioritizer sorts (5 tests)

TestSubmissionTracker: create submission, state transition, append-only history,
active excludes terminal, stats counts, weekly report markdown (6 tests)

Mock HTTP requests with unittest.mock.patch. Use tempfile for state dirs.

## DELIVERABLE
File: 06_BENCHMARKING/tests/08_CYBERSECURITY/test_bounty_engine.py

## CONSTRAINTS
- pytest, unittest.mock, tempfile, dataclasses
- NEVER make real HTTP requests
- Output valid Python only
