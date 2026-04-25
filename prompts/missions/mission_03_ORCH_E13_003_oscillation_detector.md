# MISSION: Oscillation Detector — Anti-Blind-Retry Gate
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E13_003_oscillation_detector
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The factory has historically wasted hours of compute retrying the same
failing mission against the same broken conditions. The 0.6 score wall
on 03_ORCHESTRATION missions appeared dozens of times before forensic
diagnosis identified the stale test root cause.

This mission builds an oscillation detector: when the same gate fails
3 or more times in a row for the same mission, the detector raises an
alert recommending an approach change. This prevents the factory from
burning 27B-tier inference cycles on impossible work.

The detector maintains state in a JSON file. It is called by the
orchestrator after each gate failure to record the event and check for
oscillation patterns.

## EXACT IMPORTS:
```python
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/orchestration/oscillation_detector.py`
containing:

### Constants
- DEFAULT_THRESHOLD = 3            # failures before oscillation flagged
- DEFAULT_STATE_PATH = "state/oscillation_state.json"

### Dataclass: GateFailure
Frozen dataclass with these fields:
```
mission_id: str
gate_name: str              # e.g., "hygiene", "hallucination", "logic"
failure_reason: str         # short description
timestamp: str              # ISO UTC
attempt_number: int
```

### Dataclass: OscillationAlert
Frozen dataclass with these fields:
```
mission_id: str
gate_name: str
failure_count: int
first_failure_at: str       # ISO UTC of earliest matching failure
last_failure_at: str        # ISO UTC of most recent matching failure
recommended_action: str     # one of: REWRITE_BRIEF, CHANGE_TIER, ESCALATE_TO_SOVEREIGN
rationale: str              # short human-readable explanation
```

### Class: OscillationDetector
Constructor signature:
```
__init__(self, state_path: Path = None, threshold: int = DEFAULT_THRESHOLD)
```

The constructor:
1. Stores state_path (default DEFAULT_STATE_PATH relative to repo root)
2. Stores threshold
3. Loads existing state from disk if it exists, otherwise initializes empty
4. Validates threshold >= 2, raises ValueError otherwise

Method: `record_failure(self, mission_id: str, gate_name: str, failure_reason: str, attempt_number: int) -> None`

Records a gate failure event by:
1. Constructing a GateFailure dataclass
2. Appending to internal state list
3. Persisting state to disk

Method: `check_oscillation(self, mission_id: str) -> Optional[OscillationAlert]`

Examines all recorded failures for the given mission_id. Groups them by
gate_name. If any gate has failure_count >= threshold, returns an
OscillationAlert with:
- failure_count from the most-failed gate
- first_failure_at and last_failure_at from that gate's record set
- recommended_action determined by:
  * "REWRITE_BRIEF" if hygiene or hallucination gate is oscillating
  * "CHANGE_TIER" if logic gate is oscillating (tests may be wrong)
  * "ESCALATE_TO_SOVEREIGN" if multiple gates are oscillating simultaneously
- rationale explaining which gate is stuck and what to try

Returns None if no gate has reached the threshold.

Method: `clear_mission(self, mission_id: str) -> int`

Removes all failure records for the given mission_id. Used after a
successful ratification or sovereign override. Returns the number of
records removed.

Method: `get_summary(self) -> Dict[str, int]`

Returns a dict mapping mission_id -> total failure count for all
missions currently in state. Used for reporting.

### Function: get_default_detector() -> OscillationDetector
Module-level convenience: returns an OscillationDetector with default
state path. Used by callers that don't need custom configuration.

## DELIVERABLE
File: mantis_core/orchestration/oscillation_detector.py

## BEHAVIORAL REQUIREMENTS
- State file must be created with parents=True if directory does not exist
- State file format: JSON with a "failures" key holding a list of dicts
- All timestamps timezone-aware UTC, ISO format
- record_failure must be atomic — write to temp file then rename
- check_oscillation must NOT modify state (read-only operation)
- clear_mission must persist after removal
- Threshold below 2 is invalid (must allow at least one retry)
- The detector itself never blocks dispatch — it only reports

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. Constructor raises ValueError for threshold < 2
2. record_failure persists to state file correctly
3. check_oscillation returns None for missions with < threshold failures
4. check_oscillation returns alert when threshold is reached for any gate
5. Recommended action is REWRITE_BRIEF for hygiene/hallucination oscillation
6. Recommended action is CHANGE_TIER for logic oscillation
7. Recommended action is ESCALATE_TO_SOVEREIGN for multi-gate oscillation
8. clear_mission removes only the specified mission's records
9. State file uses atomic write (temp + rename)
10. get_summary returns accurate per-mission counts

## CONSTRAINTS
- Pure stdlib (json, pathlib, datetime, dataclasses, typing)
- No external dependencies
- Atomic file writes only — never partial state
- Output valid Python only
