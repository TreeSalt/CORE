# MISSION: mantis_replay_harness
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_006_replay_harness

## DELIVERABLE
File: mantis_core/validation/replay_harness.py

## INTERFACE CONTRACT
### Class: ReplayHarness
Constructor takes: csv_path, pipeline_factory
Method: replay() -> ReplayResults
Method: replay_with_seed(seed: int) -> ReplayResults  # deterministic
