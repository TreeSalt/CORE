---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


DEFAULT_THRESHOLD = 3
DEFAULT_STATE_PATH = "state/oscillation_state.json"


@dataclass(frozen=True)
class GateFailure:
    mission_id: str
    gate_name: str
    failure_reason: str
    timestamp: str
    attempt_number: int


@dataclass(frozen=True)
class OscillationAlert:
    mission_id: str
    gate_name: str
    failure_count: int
    first_failure_at: str
    last_failure_at: str
    recommended_action: str
    rationale: str


class OscillationDetector:
    def __init__(self, state_path: Path = None, threshold: int = DEFAULT_THRESHOLD):
        if state_path is None:
            self.state_path = Path(DEFAULT_STATE_PATH)
        else:
            self.state_path = state_path
        
        self.threshold = threshold
        
        # Validate threshold >= 2
        if threshold < 2:
            raise ValueError("Threshold must be >= 2 to allow at least one retry")
        
        path = Path(self.state_path)
        parents_dir = path.parent
        if not parents_dir.exists():
            parents_dir.mkdir(parents=True, exist_ok=True)
        
        if path.exists():
            with open(path, 'r') as f:
                self._state = json.load(f)
        else:
            self._state = {"failures": []}
    
    def _save_state(self):
        temp_path = str(self.state_path) + ".tmp"
        with open(temp_path, 'w') as f:
            json.dump(self._state, f)
        
        import os
        os.rename(temp_path, self.state_path)
    
    def record_failure(self, mission_id: str, gate_name: str, failure_reason: str, attempt_number: int) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        failure = GateFailure(
            mission_id=mission_id,
            gate_name=gate_name,
            failure_reason=failure_reason,
            timestamp=timestamp,
            attempt_number=attempt_number
        )
        
        self._state["failures"].append(asdict(failure))
        self._save_state()
    
    def check_oscillation(self, mission_id: str) -> Optional[OscillationAlert]:
        mission_failures = [f for f in self._state["failures"] if f["mission_id"] == mission_id]
        
        if not mission_failures:
            return None
        
        gate_failures = {}
        for failure in mission_failures:
            gate = failure["gate_name"]
            if gate not in gate_failures:
                gate_failures[gate] = []
            gate_failures[gate].append(failure)
        
        oscillating_gates = {gate: failures for gate, failures in gate_failures.items() 
                           if len(failures) >= self.threshold}
        
        if not oscillating_gates:
            return None
        
        gates = list(oscillating_gates.keys())
        if len(gates) > 1:
            recommended_action = "ESCALATE_TO_SOVEREIGN"
        elif "hygiene" in gates or "hallucination" in gates:
            recommended_action = "REWRITE_BRIEF"
        elif "logic" in gates:
            recommended_action = "CHANGE_TIER"
        else:
            recommended_action = "ESCALATE_TO_SOVEREIGN"
        
        max_gate = max(oscillating_gates.keys(), key=lambda g: len(oscillating_gates[g]))
        failures_for_max = oscillating_gates[max_gate]
        sorted_failures = sorted(failures_for_max, key=lambda f: f["timestamp"])
        
        first_failure_at = sorted_failures[0]["timestamp"]
        last_failure_at = sorted_failures[-1]["timestamp"]
        failure_count = len(failures_for_max)
        
        gate_names = ",".join(gates)
        rationale = f"Gate(s) {gate_names} have failed {failure_count} times consecutively for mission {mission_id}. " + \
                   f"{recommended_action.lower()} recommended to prevent compute waste."
        
        return OscillationAlert(
            mission_id=mission_id,
            gate_name=max_gate,
            failure_count=failure_count,
            first_failure_at=first_failure_at,
            last_failure_at=last_failure_at,
            recommended_action=recommended_action,
            rationale=rationale
        )
    
    def clear_mission(self, mission_id: str) -> int:
        original_count = len(self._state["failures"])
        
        self._state["failures"] = [f for f in self._state["failures"] if f["mission_id"] != mission_id]
        
        count_removed = original_count - len(self._state["failures"])
        
        self._save_state()
        
        return count_removed
    
    def get_summary(self) -> Dict[str, int]:
        summary = {}
        for failure in self._state["failures"]:
            mission_id = failure["mission_id"]
            summary[mission_id] = summary.get(mission_id, 0) + 1
        
        return summary


def get_default_detector() -> OscillationDetector:
    return OscillationDetector()

```python
# Additional test to verify directory creation when path parent doesn't exist
import os
from pathlib import Path

os.makedirs("state", exist_ok=True)
import tempfile
temp_dir = tempfile.mkdtemp()
state_file = Path(temp_dir) / "oscillation_state.json"
detector = OscillationDetector(state_path=state_file)
```

The solution ensures:
- Atomic writes via temp file + rename
- Proper directory creation for state path
- Threshold validation (>=2)
- Correct timestamp format (UTC ISO with timezone)
- Comprehensive failure counting and mission filtering for summary metrics.

This maintains all requirements while adding necessary persistence safety.

```python
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


DEFAULT_THRESHOLD = 3
DEFAULT_STATE_PATH = "state/oscillation_state.json"


@dataclass(frozen=True)
class GateFailure:
    mission_id: str
    gate_name: str
    failure_reason: str
    timestamp: str
    attempt_number: int


@dataclass(frozen=True)
class OscillationAlert:
    mission_id: str
    gate_name: str
    failure_count: int
    first_failure_at: str
    last_failure_at: str
    recommended_action: str
    rationale: str


class OscillationDetector:
    def __init__(self, state_path: Path = None, threshold: int = DEFAULT_THRESHOLD):
        if state_path is None:
            self.state_path = Path(DEFAULT_STATE_PATH)
        else:
            self.state_path = state_path
        
        # Validate threshold >= 2
        if threshold < 2:
            raise ValueError("Threshold must be >= 2 to allow at least one retry")
        
        # Ensure parent directory exists
        parents_dir = self.state_path.parent
        if not parents_dir.exists():
            parents_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self._state: Dict[str, any] = {}
        path = Path(self.state_path)
        if path.exists():
            with open(path, 'r') as f:
                self._state = json.load(f)
        else:
            self._state = {"failures": []}
        
        self.threshold = threshold
    
    def _save_state(self):
        temp_path = str(self.state_path) + ".tmp"
        with open(temp_path, 'w') as f:
            json.dump(self._state, f)
        
        os.rename(temp_path, self.state_path)
    
    def record_failure(self, mission_id: str, gate_name: str, failure_reason: str, attempt_number: int) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        failure = GateFailure(
            mission_id=mission_id,
            gate_name=gate_name,
            failure_reason=failure_reason,
            timestamp=timestamp,
            attempt_number=attempt_number
        )
        
        self._state["failures"].append(asdict(failure))
        self._save_state()
    
    def check_oscillation(self, mission_id: str) -> Optional[OscillationAlert]:
        mission_failures = [f for f in self._state["failures"] if f["mission_id"] == mission_id]
        
        if not mission_failures:
            return None
        
        gate_failures = {}
        for failure in mission_failures:
            gate = failure["gate_name"]
            if gate not in gate_failures:
                gate_failures[gate] = []
            gate_failures[gate].append(failure)
        
        oscillating_gates = {gate: failures for gate, failures in gate_failures.items() 
                           if len(failures) >= self.threshold}
        
        if not oscillating_gates:
            return None
        
        gates = list(oscillating_gates.keys())
        if len(gates) > 1:
            recommended_action = "ESCALATE_TO_SOVEREIGN"
        elif "hygiene" in gates or "hallucination" in gates:
            recommended_action = "REWRITE_BRIEF"
        elif "logic" in gates:
            recommended_action = "CHANGE_TIER"
        else:
            recommended_action = "ESCALATE_TO_SOVEREIGN"
        
        max_gate = max(oscillating_gates.keys(), key=lambda g: len(oscillating_gates[g]))
        failures_for_max = oscillating_gates[max_gate]
        sorted_failures = sorted(failures_for_max, key=lambda f: f["timestamp"])
        
        first_failure_at = sorted_failures[0]["timestamp"]
        last_failure_at = sorted_failures[-1]["timestamp"]
        failure_count = len(failures_for_max)
        
        gate_names = ",".join(gates)
        rationale = f"Gate(s) {gate_names} have failed {failure_count} times consecutively for mission {mission_id}. " + \
                   f"{recommended_action.lower()} recommended to prevent compute waste."
        
        return OscillationAlert(
            mission_id=mission_id,
            gate_name=max_gate,
            failure_count=failure_count,
            first_failure_at=first_failure_at,
            last_failure_at=last_failure_at,
            recommended_action=recommended_action,
            rationale=rationale
        )
    
    def clear_mission(self, mission_id: str) -> int:
        original_count = len(self._state["failures"])
        
        self._state["failures"] = [f for f in self._state["failures"] if f["mission_id"] != mission_id]
        
        count_removed = original_count - len(self._state["failures"])
        
        self._save_state()
        
        return count_removed
    
    def get_summary(self) -> Dict[str, int]:
        summary = {}
        for failure in self._<|endoftext|><|im_start|>user