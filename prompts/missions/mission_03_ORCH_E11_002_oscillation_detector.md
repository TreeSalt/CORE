# MISSION: Oscillation Detector
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E11_002_oscillation_detector
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
A known failure mode: a mission fails the same benchmark gate repeatedly across
retries, each time generating a slightly different but fundamentally identical
wrong approach. The corrective context says "PYTEST_FAILED" but the model lacks
the architectural insight to change strategy. It oscillates instead of evolves.

Rule: if the same gate fails 3+ times, force a different approach.

## BLUEPRINT
Create an oscillation detector that integrates with the orchestrator retry loop:

1. Track failure history per mission:
   - Which gate failed (HALLUCINATION, HYGIENE, LOGIC, PYTEST)
   - The score on each attempt
   - A fingerprint of the failure (hash of the failing test names)

2. Detect oscillation:
   - If the same gate fails 3+ consecutive attempts: OSCILLATION_DETECTED
   - If the score is identical across 2+ attempts: PLATEAU_DETECTED

3. On detection, inject an APPROACH_CHANGE directive into corrective context:
   - "OSCILLATION DETECTED: You have failed the same gate 3 times with the same
     approach. You MUST use a fundamentally different algorithm or architecture.
     Do NOT refine your previous attempt — start from a different design."

4. Return an OscillationReport dataclass:
   - mission_id: str
   - attempts: int
   - oscillating: bool
   - plateau: bool
   - stuck_gate: str | None
   - directive: str | None

## DELIVERABLE
File: mantis_core/orchestration/oscillation_detector.py

## CONSTRAINTS
- Pure Python standard library (dataclasses, hashlib, json)
- Must be stateless per invocation — reads attempt history from state/ directory
- No file writes except to state/oscillation_history.json
- Output valid Python only
