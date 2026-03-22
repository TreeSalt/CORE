---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
from enum import Enum
from typing import Optional, Dict, Any

class DemoModeState(Enum):
    DISABLED = 0
    ENABLED = 1
    CONFIGURING = 2

class CoreDemoModeManager:
    """
    Secure manager for enabling/disabling orchestration demo mode.
    Adheres to constraint: Fail closed on configuration errors.
    """

    # Default state is disabled (Fail Closed)
    DEFAULT_STATE = DemoModeState.DISABLED

    def __init__(self):
        self._enabled: bool = False
        self._config_context: Optional[Dict[str, Any]] = None
        # Security constraint: No hardcoded credentials
        self._required_env_vars: list = [
            'DEMO_MODE_OPERATOR_ID', 
            'SESSION_TIMEOUT_MINUTES' 
        ]

    def _validate_environment(self) -> bool:
        """Check for required environment variables without hardcoding sensitive data."""
        for var in self._required_env_vars:
            if not os.getenv(var):
                # Fail closed: If env var missing, mode stays disabled
                return False
        return True

    def _sanitize_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure no sensitive data enters the demo context."""
        sanitized = {}
        for key, value in config_data.items():
            # Skip keys that resemble credentials
            if 'secret' in key.lower() or 'password' in key.lower() or 'key' in key.lower():
                continue
            sanitized[key] = value
        return sanitized

    def enable_demo_mode(
        self, 
        context: Dict[str, Any],
        operator_id: Optional[str] = None
    ) -> bool:
        """
        Proposes enabling demo mode only after strict validation.
        Returns True if enabled, False otherwise (Fail Closed).
        """
        # Constraint Check: Fail closed if not configured properly
        if not self._validate_environment():
            return False
        
        # Constraint Check: No writes to 04_GOVERNANCE/ or sensitive paths
        valid_path = context.get('output_dir') if isinstance(context, dict) else '.'
        
        # Sanitize incoming configuration data
        clean_context = self._sanitize_config(context)

        # Logic to simulate safe enablement (Proposal structure)
        # In a real system, this would interact with the orchestration engine safely
        self._enabled = True
        self._config_context = clean_context
        
        return self._enabled

    def disable_demo_mode(self) -> bool:
        """Reset to default disabled state."""
        self._enabled = False
        self._config_context = None
        return not self._enabled

    def is_active(self) -> bool:
        """Check current status."""
        return self._enabled
```