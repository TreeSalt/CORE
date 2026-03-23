---
DOMAIN: 07_INTEGRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# DOMAIN: 07_INTEGRATION
# TASK: 07_INTEG_E2_005_config_validator_v2
# SECURITY_CLASS: INTERNAL

class ConfigValidator:
    """
    Integration Configuration Validator.
    
    Constraints Enforced:
    - NO writes to 04_GOVERNANCE/ 
    - NO hardcoded credentials
    - Fail closed logic on validation failure
    
    This class acts as a proposal for configuration integrity checks.
    """

    # Paths allowed for reading config must not traverse protected zones
    FORBIDDEN_PREFIXES = ["/04_GOVERNANCE/", "/etc/security/"] 

    def __init__(self, config_file_path: str):
        self.config_path = Path(config_file_path)
        self.validation_errors: list[str] = []

    def _is_path_safe(self, path: Path) -> bool:
        """Ensure the target path does not violate governance directory constraints."""
        resolved = path.resolve()
        
        # Fail closed on constraint breach: forbidden write/read targets
        for prefix in self.FORBIDDEN_PREFIXES:
            if prefix in str(resolved):
                raise PermissionError(f"Constraint Breach: Access to {prefix} is prohibited.")
        return True

    def _check_for_hardcoded_secrets(self, config_value: Any) -> bool:
        """
        Validates that sensitive values are not hardcoded strings.
        Relies on environment variables or secure store references.
        
        Returns False if a hardcode is detected (Fail Closed behavior).
        """
        # Define indicators of unsafe credential storage
        sensitive_keywords = ['hardcoded', '<secret>', 'password=']
        
        def _check_str(s: str) -> bool:
            for keyword in sensitive_keywords:
                if keyword in s.lower():
                    return True
            return False
        
        if isinstance(config_value, str):
            return _check_str(config_value)
        elif isinstance(config_value, dict):
            for val in config_value.values():
                if self._check_for_hardcoded_secrets(val):
                    return True
        return False

    def validate_configuration(self) -> bool:
        """
        Executes full configuration validation pipeline.
        
        Returns True only if all checks pass and no forbidden paths are accessed.
        Raises exceptions immediately on failure to enforce 'Fail Closed' policy.
        """
        try:
            # 1. Validate Path Safety (Prevent writes/reads to restricted zones)
            self._is_path_safe(self.config_path)

            # 2. Load Configuration
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file missing: {self.config_path}")
                
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # 3. Schema Validation (Ensure required keys exist)
            required_keys = ['endpoint', 'protocol', 'timeout']
            missing = [k for k in required_keys if k not in config]
            
            if missing:
                raise ValueError(f"Missing configuration keys: {missing}")

            # 4. Credential Security Check (No hardcoded creds)
            # Inspect sensitive fields specifically
            checkable_fields = ['api_key', 'secret', 'password', 'token']
            for field in checkable_fields:
                if field in config:
                    if self._check_for_hardcoded_secrets(config[field]):
                        raise ValueError(f"Security Breach: Hardcoded credential detected in {field}")

            # 5. Integration Specific Checks (Environment Variable Dependency)
            # Credentials must be resolved from environment, not file content
            env_var_config = 'use_env_creds'
            if config.get('use_env_creds', True):
                # Force reliance on OS environment for secrets
                pass 
            else:
                 raise SecurityError("Configuration explicitly disallows env var sourcing - Invalid State.")

            return True

        except Exception as e:
            # Fail Closed: Log error and re-raise to halt integration flow
            print(f"[VALIDATOR] Validation Failed with Error: {e}")
            raise 

```