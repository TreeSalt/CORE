# MISSION: preflight_runner_v5 — E13 Re-Entry
TYPE: IMPLEMENTATION
MISSION_ID: 03_ORCH_E16_001_preflight_runner_v5

## CONTEXT
This is a re-implementation of the E13 mission preflight_runner that
failed with hallucinated import paths and function name drift. See
state/sovereign_vault/e14_backlog/E14_BACKLOG_002_preflight_runner_v5.json
for the failure analysis.

The original brief is at prompts/missions/mission_03_ORCH_E13_001_preflight_runner.md
— follow it EXACTLY with the amendments below.

## EXACT IMPORT FOR THE DOCTOR MODULE
The previous attempt hallucinated `from manticore.core.modules.doctor`.
That package DOES NOT EXIST. The correct import is:
```python
from mantis_core.orchestration.core_doctor import CoreDoctor
```
DO NOT confabulate any other path. The module is at
mantis_core/orchestration/core_doctor.py and it exists today.

## EXACT FUNCTION NAMES REQUIRED
The deliverable file MUST define EXACTLY these names. No variants accepted:
- check_disk_space
- check_governor_seal
- check_ollama_health
- check_vram_available
- check_doctor
- run_preflight

If you write `verify_doctor_module` instead of `check_doctor`, the gate
will reject the proposal.

## DELIVERABLE
File: scripts/preflight_runner.py

Follow the original brief at prompts/missions/mission_03_ORCH_E13_001_preflight_runner.md
for the dataclass definitions, behavioral requirements, and CLI entry point.
