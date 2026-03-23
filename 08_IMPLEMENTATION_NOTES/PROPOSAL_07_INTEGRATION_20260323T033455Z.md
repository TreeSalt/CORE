---
DOMAIN: 07_INTEGRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# PROPOSAL: 07_INTEG_E2_003_domain_wiring_config.py
# SECURITY_CLASS: INTERNAL
# DOMAIN: 07_INTEGRATION
# STATUS: DRAFT_PROPOSAL (Read-Only Validation)

import os
import sys
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

class IntegrationConstraintViolationError(Exception):
    """Custom exception raised when security constraints are breached."""
    pass

class SecurityConstraintValidator:
    """Ensures compliance with domain-specific constraints."""

    def __init__(self, forbidden_paths: str = "04_GOVERNANCE/"):
        self.forbidden_paths = [forbidden_paths]

    def validate_path(self, path: str) -> bool:
        """Ensure file paths do not write to restricted directories."""
        for forbidden in self.forbidden_paths:
            if path.startswith(forbidden):
                raise IntegrationConstraintViolationError(
                    f"Path violation detected: {path} starts with forbidden directory {forbidden}"
                )
        return True

    def validate_credentials(self, secret_value: str) -> bool:
        """Ensure no hardcoded secrets in string literals (Simulation)."""
        # In a real proposal, this checks the code generation context.
        # Here we validate against environment variables.
        if secret_value.startswith("sk_") or secret_value.startswith("ak_"):
            raise IntegrationConstraintViolationError(
                "Hardcoded credential pattern detected in configuration value."
            )
        return True

class DomainWiringProposal:
    """Generates a proposal for integrating domain components."""

    def __init__(self, validator: SecurityConstraintValidator):
        self.validator = validator
        self.connections: List[Dict[str, any]] = []
        self.environment: Dict[str, str] = {}

    def load_configuration(self, connection_config: Dict) -> None:
        """Safely loads a connection configuration proposal."""
        # Constraint Check: Path Safety
        target_path = connection_config.get("storage_path", "")
        if not self.validator.validate_path(target_path):
            raise IntegrationConstraintViolationError(
                f"Invalid path: {target_path}"
            )

        # Constraint Check: Credential Safety
        credentials = connection_config.get("credentials", {})
        for key, value in credentials.items():
            if isinstance(value, str) and len(value) > 0:
                self.validator.validate_credentials(value)
        
        # Store as proposal (no write operation yet)
        self.connections.append({
            "type": connection_config.get("type"),
            "endpoint": connection_config.get("endpoint"),
            "auth_method": "env_ref",
            "status": "pending_approval"
        })

    def get_proposal_manifest(self) -> Dict:
        """Returns the structure of the proposed wiring."""
        return {
            "domain_id": "07_INTEGRATION",
            "task_id": "07_INTEG_E2_003_domain_wiring",
            "connection_count": len(self.connections),
            "security_class": "INTERNAL",
            "constraints_applied": [
                "No writes to 04_GOVERNANCE/",
                "No hardcoded credentials",
                "Fail closed on violation"
            ],
            "connections_schema": self._get_safe_schema()
        }

    def _get_safe_schema(self) -> Dict:
        """Generates a schema definition for connections without sensitive data."""
        schema = {
            "connection_type": "str",
            "endpoint": "str (URL or API Path)",
            "auth_ref": {"key": "str", "source": "ENV_VAR"}
        }
        return schema

def main_proposal():
    """Main execution function for the proposal validation."""
    # Initialize Validator with constraint rules
    validator = SecurityConstraintValidator(forbidden_paths="04_GOVERNANCE/")
    
    # Initialize Proposal Handler
    handler = DomainWiringProposal(validator)

    try:
        # Define a safe configuration structure (Example Usage)
        proposed_config = {
            "type": "api_gateway",
            "endpoint": os.getenv("INTERNAL_API_ENDPOINT", "https://localhost:8080/"), 
            "credentials": {
                # Constraint: No hardcoded values, use placeholders for env vars
                "api_key_env_var": "API_KEY_SECRET_VAR"
            },
            "storage_path": "/data/integration_logs" # Safe path
        }

        # Load the proposal (Read-only context)
        handler.load_configuration(proposed_config)
        
        # Output Manifest
        manifest = handler.get_proposal_manifest()
        print("PROPOSAL GENERATED SUCCESSFULLY")
        print(f"Task ID: {manifest['task_id']}")
        print(f"Connections Defined: {manifest['connection_count']}")
        
    except IntegrationConstraintViolationError as e:
        # Fail closed on constraint breach
        sys.stderr.write(f"FATAL: Constraint breached - Execution halted.\n")
        sys.stderr.write(str(e))
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main_proposal())
```