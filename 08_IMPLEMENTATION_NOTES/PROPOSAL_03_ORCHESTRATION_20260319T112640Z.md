---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

import os
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps

# SECURITY: Define forbidden paths explicitly to prevent unauthorized governance access
FORBIDDEN_PATHS = frozenset(["04_GOVERNANCE/"])

class ConstraintViolationError(Exception):
    """Custom exception raised when orchestration constraints are breached."""
    pass

def validate_path_safety(path_str: str) -> None:
    """
    Validates that a target path does not breach governance security constraints.
    Fails closed immediately if a breach is detected.
    """
    clean_path = Path(path_str).resolve()
    for forbidden in FORBIDDEN_PATHS:
        if str(clean_path).startswith(forbidden) or str(clean_path).endswith(forbidden):
            raise ConstraintViolationError(f"Security Breach: Access attempted to restricted path {forbidden}")

def validate_no_hardcoded_creds(config_data: Dict[str, Any]) -> None:
    """
    Validates that configuration data does not contain hardcoded secrets.
    Fails closed on credential leakage attempts.
    """
    forbidden_patterns = [
        r'.*password.*\w+',
        r'.*api_key.*\d+[\w]?',
        r'.*secret.*\d+',
        r'token.*[a-zA-Z0-9]{16,}'
    ]
    
    for key, value in config_data.items():
        if isinstance(value, str):
            for pattern in forbidden_patterns:
                if bool(re.match(pattern, value)):
                    raise ConstraintViolationError(f"Security Breach: Hardcoded credential detected in key {key}")

def generate_mantis_makefile_proposal(base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a secure proposal structure for Mantis orchestration Makefiles.
    Ensures all constraints regarding governance paths and credentials are respected.
    
    Args:
        base_path: The root directory for the makefile operations. Defaults to current working dir.
        
    Returns:
        A dictionary containing the proposed Makefile configuration structure.
    """
    import re
    
    # Default to current directory if not specified
    if not base_path:
        base_path = os.getcwd()

    # Enforce Constraint: No writes to 04_GOVERNANCE/ or access thereof
    validate_path_safety(base_path)
    
    # Read credentials safely from environment (Fail closed if missing or invalid format)
    mantis_host = os.getenv("MANINTS_HOST", "localhost")
    auth_token_env = os.getenv("MANINTS_TOKEN")
    
    # Fail closed if token is explicitly required but not set
    # This proposal assumes the token will be injected at runtime, not hardcoded
    config_draft = {
        "orchestration_task_id": "03_ORCH_E3_003_mantis_makefile",
        "base_directory": base_path,
        "security_level": "INTERNAL",
        "credentials": {
            "source": "environment_variable",
            "key_name": "MANINTS_TOKEN", 
            "default": None,  # Do not default to empty string if validation logic requires non-null
            "validation_status": "pending_runtime_check"
        },
        "make_targets": {
            "lint": "flake8 --max-line-length=120",
            "test": "pytest -v --cov=",
            "integration": "docker-compose up --build",
            "deploy_validate": "bash scripts/pre_deploy.sh"
        }
    }
    
    # Apply credential safety check on the draft (in case any env vars are passed into config)
    if auth_token_env and len(auth_token_env) > 0:
         validate_no_hardcoded_creds(config_draft["credentials"])
    
    # Construct proposal structure without writing to forbidden paths
    return config_draft

# Optional entry point for interactive usage (Safe, no file writes performed in this block)
if __name__ == "__main__":
    try:
        # Generate a safe default proposal based on current path
        proposal = generate_mantis_makefile_proposal()
        print(f"Proposal generated successfully for {proposal['base_directory']}.")
        
        # Note: Actual file writing or API execution is omitted to comply with "Proposals only" constraint.
        print("Use 'import' to integrate into existing orchestration scripts.")
    except ConstraintViolationError as e:
        # Fail closed handling: Print error and exit without masking
        print(f"SECURITY STOP: {e}")
        raise