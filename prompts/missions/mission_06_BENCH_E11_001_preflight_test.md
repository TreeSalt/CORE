# MISSION: Test Suite — CORE Hardening Modules
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E11_001_preflight_test
TYPE: TEST
VERSION: 1.0

## CONTEXT
Test suites for mission preflight, oscillation detector, and core doctor.

## BLUEPRINT
TestMissionPreflight: valid brief passes, missing domain fails, governance path
rejected, empty brief fails, hash computed, invalid extension warns (7 tests)

TestOscillationDetector: no oscillation on first attempt, oscillation after 3 same
gate, plateau on identical scores, directive generated, different gates no trigger (5 tests)

TestCoreDoctorImport: importable, returns structured report (2 tests)

## DELIVERABLE
File: 06_BENCHMARKING/tests/03_ORCHESTRATION/test_core_hardening.py

## CONSTRAINTS
- pytest, import from mantis_core.orchestration modules
- Self-contained with temp files
- Output valid Python only
