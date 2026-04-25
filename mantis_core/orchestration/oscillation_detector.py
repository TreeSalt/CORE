import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Any

# Define the OscillationReport dataclass with required fields and defaults for new attempts.
@dataclass(frozen=True)
class OscillationReport:
    attempt: int = 0           # The count of attempts (1-based index in history)
    mission_id: str = ""       # The specific mission identifier
    score: int = 0             # Score achieved in this attempt
    failing_tests: List[str] = field(default_factory=list)              # Tests that failed
    oscillating: bool = False  # True if stuck on a gate >3 times consecutively
    plateau: bool = False      # True if score is same as previous attempt
    stuck_gate: Optional[str] = None   # The name of the problematic gate (if oscillation)

# State manager to persist history across attempts.
def _get_mission_state_file(path_base: Path, mission_id: str) -> Path:
    """Returns the JSON state file path for a specific mission."""
    directory = path_base / "state" / mission_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "history.json"

def compute_report(mission_id: str, gate_failed: str, score: int, failing_tests: List[str]) -> OscillationReport:
    """
    Computes the report for an attempt. 
    
    Args:
        mission_id (str): The ID of the mission being run.
        gate_failed (str): Name of the gate that failed this attempt.
        score (int): Score achieved.
        failing_tests (List[str]): List of names of failing tests in this attempt.
    
    Returns:
        OscillationReport: The report for this specific attempt including status flags.
    """
    base_path = Path(".")  # Store state in current directory's 'state' folder
    
    file_path = _get_mission_state_file(base_path, mission_id)
    
    # Initialize history if file doesn't exist or is empty/invalid JSON
    try:
        with open(file_path, "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    # Append new attempt to history
    new_attempt_record = {
        "mission_id": mission_id,
        "score": score,
        "failing_tests": failing_tests,
        "gate_failed": gate_failed  # Track the specific gate that failed for oscillation logic
    }
    
    history.append(new_attempt_record)
    
    # Check oscillation: 3 consecutive failures on same gate. 
    # We check from the most recent failure backwards.
    # If current attempt is a failure (check if 'gate_failed' implies failure or just track score drop?),
    # Actually, prompt says "failed the same gate". 
    # We assume if we are in this function, we have failed. 
    # But let's be robust: check consecutive failures on the SAME gate.
    
    oscillating = False
    plateau = False
    stuck_gate = None
    
    # Only analyze if we have at least 2 attempts to compare for plateaus
    if len(history) >= 2:
        current_score = history[-1]["score"]
        prev_score = history[-2]["score"]
        
        # Plateau detection: Score same as previous attempt
        if current_score == prev_score:
            plateau = True
        
        # Oscillation detection: 
        # We look for a sequence of 3 consecutive failures on the SAME gate.
        # Note: The 'gate_failed' field tracks what failed *now*.
        # We need to find the most recent failure and see if previous 2 were same gate.
        
        current_gate = history[-1]["gate_failed"]
        
        # Check backwards from current attempt to find streak of failures on current_gate
        count_same_failures = 0
        temp_count = 0
        
        for i in range(len(history) - 1, -1, -1):
            attempt = history[i]
            gate = attempt["gate_failed"]
            
            # If this attempt was a failure (implied by presence of gate_failed and score != max?) 
            # Actually, we check specifically if it's a failure on THIS gate.
            # If the previous attempts passed (score high) or failed on DIFFERENT gates, break streak?
            # The prompt says "failed the same gate".
            
            # Check if this attempt was a failure and on same gate as current
            # Assuming 'gate_failed' exists -> it's a failure.
            # If score is max (success)? Let's assume if score < some threshold or just use logic.
            # But prompt implies "failed" -> implies we failed.
            # Let's count consecutive failures on same gate ending with this attempt.
            
            # Wait, what if previous attempt also had a failure?
            # The code logic below checks strict equality.
            
            if gate == current_gate:
                # We assume this is a failure (since we recorded the failed gate).
                count_same_failures += 1
                temp_count = len(history) - i
            else:
                break
        
        # If we found at least 3 failures on same gate consecutively
        if count_same_failures >= 3:
            oscillating = True
            stuck_gate = current_gate

    # Create report object
    report = OscillationReport(
        attempt=len(history),      # Total attempts made so far for this mission
        mission_id=mission_id,
        score=score,
        failing_tests=failing_tests if failing_tests else [],
        oscillating=oscillating,
        plateau=plateau,
        stuck_gate=stuck_gate if stuck_gate else None
    )
    
    # Persist updated history back to file
    with open(file_path, "w") as f:
        json.dump(history, f)
        
    return report
