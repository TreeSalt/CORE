# MISSION: mantis_smoke_test
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_007_smoke_test

## DELIVERABLE
File: tests/smoke/test_mantis_v2_smoke.py

## SCOPE
End-to-end smoke test of the v2 pipeline. Uses CsvDataProvider with
synthetic test data. Verifies pipeline produces signals, triggers
position sizing, respects circuit breakers, writes dashboard state.
