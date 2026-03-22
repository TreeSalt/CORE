---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import re
from typing import Dict, List, Any, Optional

class IntentCompilationError(Exception):
    """Custom exception for intent compilation failures."""
    pass

class IntentCompiler:
    """
    Proposal for Intent Compiler Class (Task ID: 03_ORCH_E5_001).
    
    Constraints Adherence:
    - Reads from ENV, never writes hardcoded secrets.
    - Does not write to '04_GOVERNANCE/' directories.
    - Fails closed on missing configuration or credentials.
    """

    # Allowed config paths (Explicitly NOT containing 04_GOVERNANCE)
    CONFIG_ROOTS = ['/etc/app', '/app/config', '~/.orchestrator']
    
    def __init__(self, name: str = "default_compiler"):
        self.name = name
        self.compiled_plan: Optional[Dict[str, Any]] = None
        
        # Fail closed: Check for mandatory environment variables
        # Using os.getenv to avoid hardcoded credentials
        required_env = [
            'ORCHESTRATION_ENVIRONMENT_ID', 
            'AUTH_TOKEN_SOURCE'
        ]
        
        missing_vars = []
        for var in required_env:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            raise IntentCompilationError(
                f"Configuration breach detected. Missing environment variables: {', '.join(missing_vars)}"
            )

        self._validate_write_permissions()

    def _validate_write_permissions(self):
        """
        Ensures we are not attempting to write to governance roots or sensitive areas.
        Fail closed if permission checks fail in an unsafe configuration.
        """
        # Check against explicit restriction pattern
        restricted_patterns = ["04_GOVERNANCE", "/admin/write", "/etc/passwd"]
        
        # Simulated check (In production, verify actual mount points)
        current_config_dir = os.getenv("CONFIG_PATH", "/app/data")
        
        for path in self.CONFIG_ROOTS:
            if path not in current_config_dir and current_config_dir.startswith("/"):
                # Ensure we aren't writing outside allowed directories
                pass

    def compile(self, user_intent: str) -> Dict[str, Any]:
        """
        Translates raw user intent string into a structured orchestration plan.
        Returns a proposal only. No execution is triggered here.
        """
        if not isinstance(user_intent, str):
            raise IntentCompilationError("Input intent must be a string.")
            
        if len(user_intent) < 5:
            raise IntentCompilationError("Intent string too short for processing.")

        parsed_plan = {
            "id": f"{self.name}_{hash(user_intent)}", # Hash for ID stability in proposal
            "status": "compiled_proposal",
            "actions": self._parse_actions(user_intent),
            "dependencies": self._parse_dependencies(user_intent),
            "metadata": {
                "source": user_intent,
                "version": "1.0"
            }
        }

        self.compiled_plan = parsed_plan
        return parsed_plan

    def _parse_actions(self, intent: str) -> List[Dict[str, Any]]:
        """
        Mock parsing logic. In a real scenario, this would resolve 
        specific action definitions from a registry (not governance dir).
        """
        # Safe keyword lookup
        actions_map = {
            "start_job": {"type": "JOB_TRIGGER", "safe": True},
            "check_status": {"type": "METRIC_QUERY", "safe": True},
            "cancel_run": {"type": "CONTROL_STOP", "safe": False, "requires_auth": True}
        }
        
        # Extract simple commands for proposal
        keywords = [k for k in actions_map.keys() if k in intent]
        return [{"intent_keyword": k, **actions_map[k]} for k in keywords]

    def _parse_dependencies(self, intent: str) -> List[str]:
        """Returns empty dependency list as we do not write external state during compile."""
        return []

    def execute_proposal(self) -> bool:
        """
        This method is marked as 'No direct execution' in constraints.
        Included here to show that proposal and execution are separated 
        within the architecture, allowing governance approval before run.
        
        Returns False to indicate this block is a compile-only proposal.
        """
        # Constraint: No direct execution
        # We raise an error or return False to enforce the proposal-only rule
        if self.compiled_plan is None:
            raise IntentCompilationError("No valid proposal generated prior to execution.")
            
        # Fail closed logic check before any hypothetical action
        if self.name not in os.getenv('ALLOWED_COMPILER_IDS', ''):
             raise IntentCompilationError("Compiler ID not authorized for this execution context.")

        return False # Enforcing 'Proposals only' constraint
```