---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import sys
import re
from pathlib import Path
from typing import Dict, Any

# -----------------------------------------------------------------------------
# Constraint Definitions & Constants
# -----------------------------------------------------------------------------

FORBIDDEN_ROOT = "04_GOVERNANCE"

# Forbidden path pattern regex for dynamic checks if needed. 
# This ensures no traversal to protected directories occurs.
FORBIDDEN_PATH_PATTERN = re.compile(rf'.*/{re.escape(FORBIDDEN_ROOT)}/?')

# Required Environment Variables for execution context.
REQUIRED_ENV_VARS = [
    "API_KEY",          # Generic auth token
    "SOURCE_URL",       # Data ingestion URL
]

# -----------------------------------------------------------------------------
# Custom Exceptions for Fail-Closed Behavior
# -----------------------------------------------------------------------------

class ConstraintViolationError(Exception):
    """Base exception raised when harness constraints are breached."""
    pass

class HardcodedSecretException(ConstraintViolationError):
    """Raised when credentials are hardcoded instead of fetched from environment."""
    def __init__(self, message: str = "Hardcoded secret detected"):
        self.message = message
        super().__init__(message)

class UnauthorizedPathAccessError(ConstraintViolationError):
    """Raised when attempting to write/read within forbidden directories."""
    pass

class MissingEnvVarException(ConstraintViolationError):
    """Raised when required environment variables are not set."""
    def __init__(self, missing_vars: list):
        self.missing_vars = missing_vars
        super().__init__(f"Missing required environment variables: {', '.join(missing_vars)}")

# -----------------------------------------------------------------------------
# Harness Module Proposal
# -----------------------------------------------------------------------------

class PaperTradeIngestHarness:
    """
    Secure data ingestion harness for simulated trade execution.
    Enforces constraints against writing to restricted directories
    and avoids hardcoding credentials.
    
    This module serves as a proposal for 01_DATA_E5_001_paper_trade_harness.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize harness and validate internal state against constraints."""
        self.config = config or {}
        
        # Fail closed immediately on constraint breach during init
        self._validate_constraints()

    def _validate_constraints(self) -> None:
        """
        Performs strict validation checks.
        
        Constraints enforced:
        1. No hardcoded credentials.
        2. No writes to forbidden paths (04_GOVERNANCE/).
        """
        # Check for missing environment variables
        missing = []
        for var in REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing.append(var)
        if missing:
            raise MissingEnvVarException(missing)

        # Check for hardcoded secrets in config (Fail closed if found)
        # Heuristic: Keys containing 'key', 'secret', 'password' with string values > 0
        sensitive_key_regex = re.compile(r'(key|secret|password|token)', re.IGNORECASE)
        for key, value in self.config.items():
            if isinstance(value, str):
                is_sensitive = sensitive_key_regex.search(key)
                if is_sensitive and len(value.strip()) > 0:
                    raise HardcodedSecretException(f"Hardcoded secret detected in config key: {key}")

    def initialize(self) -> None:
        """
        Proposal stub for initialization.
        
        Actual ingestion logic is injected here during runtime.
        This ensures no execution logic violates constraints (e.g., writing to 04_GOVERNANCE).
        """
        # Placeholder for logic that would use self.config['SOURCE_URL'] and API_KEY from env
        
        # Path validation check before any file operations would occur
        output_path_str = self.config.get('OUTPUT_PATH', '')
        if output_path_str:
            resolved_path = Path(output_path_str).resolve()
            
            # Fail closed if path attempts to traverse forbidden zones
            if FORBIDDEN_ROOT in str(resolved_path):
                raise UnauthorizedPathAccessError(f"Path {output_path_str} is restricted.")

    def ingest_data(self, data_source: str) -> None:
        """
        Stub method for data ingestion.
        
        This is a placeholder for the actual proposal logic.
        It does not contain implementation that writes to disk yet.
        """
        # Implementation would follow secure patterns here.
        pass

# -----------------------------------------------------------------------------
# Entry Point for Proposals (Fail Closed Logic)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        # Initialize harness with config (could be loaded from env or passed)
        harness_config = {
            'SOURCE_URL': os.getenv('SOURCE_URL'), 
            'OUTPUT_PATH': '/tmp/data' # Example safe path
        }
        
        # Ensure API_KEY exists before passing to harness to avoid hardcoding in snippet
        api_key = os.getenv('API_KEY', '')
        if not api_key:
            print("Warning: API_KEY environment variable is missing.", file=sys.stderr)
        
        harness_config['API_KEY'] = api_key

        harness = PaperTradeIngestHarness(config=harness_config)
        harness.initialize()
        
        # If successful, proceed with ingestion logic (not included in this snippet for brevity)
        
    except ConstraintViolationError as e:
        # Fail closed: exit with error code 1 to prevent execution of compromised harness
        sys.exit(1)
```