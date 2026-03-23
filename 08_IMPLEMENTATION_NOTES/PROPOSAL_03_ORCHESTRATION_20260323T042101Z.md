---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import json
import sys

# Constraint Configuration
FORBIDDEN_PATHS = ["/04_GOVERNANCE/"]
MISSION_TASK_ID = "03_ORCH_E7_006_mission_stats"

class MissionStatsProposer:
    def __init__(self):
        self._validate_environment()
        
    def _validate_environment(self):
        """Ensure no hardcoded credentials and forbidden path access."""
        # Check for environment variables to prevent credential leakage
        required_vars = ["MISSION_API_KEY", "MISSION_SECRET"]
        for var in required_vars:
            if not os.getenv(var):
                raise PermissionError(f"Constraint Breach: Missing environment variable {var}. No execution without credentials.")
            
            # Prevent hardcoded checks from being stored or logged improperly
            val = os.getenv(var)
            if len(val) == 0:
                 raise ValueError("Constraint Breach: Empty credential detected.")

    def _check_write_path(self, path):
        """Ensure no writes to forbidden governance paths."""
        for forbidden in FORBIDDEN_PATHS:
            if forbidden in path:
                raise SecurityError(f"Constraint Breach: Write attempt blocked at path {path} containing {forbidden}.")
        return True

    def propose_stats_collection(self, mission_data):
        """
        Propose a structure for collecting mission statistics.
        Returns a proposal dictionary instead of executing sensitive operations directly.
        """
        if not isinstance(mission_data, dict):
            raise TypeError("Input data must be a dictionary.")

        # Construct safe file path based on input (no governance writes)
        output_dir = os.getenv("MISSION_OUTPUT_DIR", "/tmp/metrics")
        self._check_write_path(output_dir)
        
        proposal = {
            "task_id": MISSION_TASK_ID,
            "status": "PROPOSED",
            "metrics_schema": {
                "timestamp": datetime.now().isoformat(),
                "source": "mission_stats_handler",
                "fields": [
                    "execution_time_ms",
                    "resource_utilization_pct",
                    "error_count"
                ]
            },
            "action_plan": [
                "1. Validate input data types.",
                "2. Aggregate metrics from telemetry source.",
                "3. Sanitize logs before processing.",
                "4. Generate JSON report to designated output bucket."
            ],
            "compliance_check": {
                "forbidden_paths_bypassed": True,
                "credentials_verified": True,
                "propose_only_mode": True
            }
        }

        return proposal

    def validate_data_constraints(self, data):
        """Validates incoming data against security policies."""
        if not data:
            raise ValueError("Constraint Breach: Empty input data.")
        
        # Ensure no sensitive keys are present in the data payload
        sensitive_keywords = ["password", "secret", "key"]
        for key, value in data.items():
            if isinstance(value, str):
                lower_val = value.lower()
                for keyword in sensitive_keywords:
                    if keyword in lower_val:
                        raise SecurityError(f"Constraint Breach: Sensitive keyword '{keyword}' detected in key/value.")
        
        return True

if __name__ == "__main__":
    try:
        # Initialize handler with constraint checks
        proposer = MissionStatsProposer()
        
        # Example input data (simulating mission stats context)
        mission_data = {
            "mission_id": "M-2023-X",
            "duration_hours": 4,
            "status": "active"
        }

        # Validate constraints
        proposer.validate_data_constraints(mission_data)
        
        # Generate proposal
        result = proposer.propose_stats_collection(mission_data)
        
        # Output valid Python dict representation (Proposal only)
        print(json.dumps(result, indent=4))

    except (PermissionError, SecurityError, ValueError, TypeError) as e:
        sys.exit(f"FATAL CONSTRAINT BREACH: {e}")
    except Exception as e:
        # Fail closed on any other unexpected breach
        sys.exit(f"UNEXPECTED ERROR - FAIL CLOSED: {e}")
```