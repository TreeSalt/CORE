# MISSION: Oscillation Detector for Retry Loop
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: orchestration/oscillation_detector.py

## REQUIREMENTS
- OscillationDetector class
- record_failure(mission_id, gate_name, attempt_num) -> None
- is_oscillating(mission_id, threshold) -> bool: True if same gate failed threshold+ times
- get_recommendation(mission_id) -> str: suggests "change_tier", "rewrite_brief", or "escalate"
- Maintains in-memory history, resetable per mission
- No external calls
- Output valid Python only
