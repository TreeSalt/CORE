# MISSION: CPCV Validator Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/06_BENCHMARKING/test_cpcv_validator.py

## REQUIREMENTS
- test_split_count: verify generate_splits returns correct number of splits for N=6, k=2
- test_no_overlap: verify train and test indices never overlap within a split
- test_purge_removes_leakage: verify purging removes training samples that overlap test evaluation times
- test_embargo_gap: verify embargo creates a gap between test and next train window
- Use pytest, no external calls
- Output valid Python only
