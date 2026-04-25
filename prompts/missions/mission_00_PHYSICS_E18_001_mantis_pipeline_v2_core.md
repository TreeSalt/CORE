# MISSION: mantis_pipeline_v2_core
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_001_mantis_pipeline_v2_core

## CONTEXT
Implementation of the MANTIS v2 pipeline designed in E15.M4 and refined
through E17 architecture work. Uses dependency injection.

## DELIVERABLE
File: mantis_core/pipeline.py

## INTERFACE CONTRACT
### Class: MantisLivePipeline
Constructor takes: data_provider, regime_detector, trend_signal,
position_sizer, executor, circuit_breakers (all injected, no module-level imports)

Methods:
- run_step() — process one tick
- run_continuous(stop_signal) — main loop
- get_state() -> dict — current pipeline state for dashboard

## CONSTRAINTS
- All dependencies injected, no module-level singletons
- Must be testable with mock providers
- Must respect circuit breakers
