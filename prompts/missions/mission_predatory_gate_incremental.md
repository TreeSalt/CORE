# MISSION: Predatory Gate Batch Runner v2
DOMAIN: 06_BENCHMARKING
TASK: implement_predatory_gate_batch_v2
TYPE: IMPLEMENTATION
VERSION: 2.0

## CONTEXT
The Predatory Gate v2 runner exists at scripts/run_predatory_gate.py.
However, new strategies (E2.5 resurrections + E3 pairs) were just ratified
and need to be tested. The current runner discovers strategies from
proposals but doesn't distinguish which have already been tested.

## BLUEPRINT
Create an incremental gate runner that:
1. Reads state/PREDATORY_GATE_REPORT.json for already-tested strategies
2. Scans 08_IMPLEMENTATION_NOTES/ for RATIFIED proposals NOT in the report
3. Runs ONLY the new untested strategies through all 4 scenarios
4. Merges results into the existing PREDATORY_GATE_REPORT.json
5. Updates state/predatory_gate_survivors.json with new survivors
6. Updates state/champion_registry.json with new entries

This enables incremental testing: run the gate after every factory batch
without re-testing strategies that already passed or failed.

## DELIVERABLE
File: scripts/run_predatory_gate_incremental.py

## CONSTRAINTS
- Must preserve existing report data (append, not overwrite)
- Must use .venv/bin/python3 (numpy/pandas in venv)
- Use same scenario generators as run_predatory_gate.py
- Same BaseStrategy shim for E1-era code
- Output valid Python only
