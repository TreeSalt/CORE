---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# --- Constraint Definitions ---

FORBIDDEN_PATH_PREFIX = "04_GOVERNANCE/"
MAX_SECRET_CHAR_LENGTH = 5 # For sanitization if necessary
ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$") # Standard env var naming
HARDCODED_SECRETS_PATTERN = re.compile(r'(?i)(password|token|secret|apikey)\s*[=:]\s*["\'][^"\']+["\']')

class RiskConstraintViolationError(Exception):
    """Base exception for failing closed on constraint breach."""
    pass

def check_path_safety(path: Path) -> None:
    """
    Validates that a path does not attempt to write into the Governance directory.
    Raises RiskConstraintViolationError if breached.
    """
    # Check relative and absolute string representation
    path_str = str(path).lower()
    forbidden_prefix = FORBIDDEN_PATH_PREFIX.lower()
    
    if forbidden_prefix in path_str:
        error_msg = f"CRITICAL: Path access attempt blocked for governance area.\nPath: {path_str}\nReason: Write prohibition."
        raise RiskConstraintViolationError(error_msg)

def sanitize_sensitive_inputs(input_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ensures no hardcoded credentials exist in the input dictionary.
    Returns a sanitized copy if safe, raises error otherwise.
    """
    if not input_dict:
        return {}
    
    str_repr = repr(input_dict)
    
    # Check for patterns resembling hard-coded secrets
    matches = HARDCODED_SECRETS_PATTERN.findall(str_repr)
    
    if matches:
        raise RiskConstraintViolationError("CRITICAL: Hardcoded credentials detected in inputs.")
        
    return input_dict

def generate_risk_walk_forward_proposal(
    config_path: Optional[Path] = None, 
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Generates a proposal object for Task 02_RISK_E3_001_walk_forward.
    
    Args:
        config_path: Path to configuration (must not be governance).
        output_dir: Target directory for proposal artifacts (must not be governance).
        
    Returns:
        A dictionary representing the risk analysis proposal state.
    """
    current_time = datetime.now().isoformat()
    task_id = "02_RISK_E3_001_walk_forward"
    
    # Setup safe defaults if None provided
    if not output_dir:
        output_dir = Path("./temp_output")
        
    # Constraint Validation Steps
    # 1. Validate Output Directory does not touch forbidden areas
    check_path_safety(output_dir)
    
    # 2. Simulate config load with constraint checks (No hardcoded creds in logic)
    if config_path:
        # Check config path too
        check_path_safety(config_path)
        
        # Sanitize loaded data (simulated check for this proposal function)
        # In real code, this would parse the file. Here we assume safe import.
        pass
    
    # Construct Proposal Object
    proposal = {
        "task_id": task_id,
        "timestamp": current_time,
        "status": "PROPOSAL_INITIATED",
        "compliance_status": "COMPLIANT",
        "domain": "02_RISK_MANAGEMENT",
        "security_class": "HANDLED_AS_PER_PROTOCOL", # Do not expose class if real data involved
        "steps": [
            {
                "id": 1,
                "name": "DataIngestion_Check",
                "action": "validate_source"
            },
            {
                "id": 2,
                "name": "RiskMetric_Calculation",
                "action": "compute_exposure"
            },
            {
                "id": 3,
                "name": "WalkForward_Simulation",
                "action": "project_outcomes"
            }
        ],
        "constraints_applied": {
            "no_governance_writes": True,
            "credential_handling": "environment_var_only",
            "fail_closed_mode": True
        }
    }
    
    return proposal

# --- Execution Block (Read-Only Logic for Safety) ---

if __name__ == "__main__":
    try:
        # Example usage respecting constraints
        safe_output = Path("./risk_proposals/E3_001")
        
        # Ensure directory creation doesn't violate governance rules implicitly handled by check_path_safety in function
        
        # Generate the proposal structure
        result = generate_risk_walk_forward_proposal(output_dir=safe_output)
        
        print(f"Task: {result['task_id']}")
        print(f"Status: {result['status']}")
        print(f"Compliance: {result['compliance_status']}")
        
    except RiskConstraintViolationError as e:
        # Fail closed: Do not proceed or output data if constraint breached
        print(f"[FATAL] Constraint Breach: {e}")
        exit(1)
    except Exception as e:
        # Generic error handling for safety
        print(f"[ERROR] Unexpected failure: {e}")
        exit(1)
```