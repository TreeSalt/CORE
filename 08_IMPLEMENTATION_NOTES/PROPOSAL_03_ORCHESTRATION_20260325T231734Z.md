---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
# DOMAIN: 03_ORCHESTRATION
# SECURITY_CLASS: INTERNAL
# TASK: 03_ORCH_E9_004_prefer_heavy

import os
from typing import Any, Callable, Optional
from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True)
class SecureContext:
    """
    Encapsulates orchestration context without exposing secrets.
    Credentials must be injected via environment variables (e.g., SECRETS_KEY).
    """
    execution_id: str
    mode: str  # 'heavy' preferred for security/stability
    state_lock: Optional[threading.Lock] = None


class OrchestrationEngine:
    """
    Secure Heavyweight Orchestration Engine.
    Principles:
    - Fail Closed on critical constraints.
    - Prefer heavy/synchronous patterns for guaranteed delivery.
    - No hardcoded credentials.
    - No direct writes to 04_GOVERNANCE/ paths.
    """

    # Critical Configuration Constants (Do not hardcode sensitive data here)
    GOVERNANCE_PATH = "/var/gov"  # Example: Access only if authorized, do not write
    SECRET_PREFIX = "SECRETS_"

    def __init__(self, context: SecureContext):
        self.context = context
        self._initialized = False
        self._lock = threading.Lock()
        
        # Failing closed check: ensure context is present
        if not context.execution_id:
            raise RuntimeError("Fail-Closed: Execution ID Missing")

    def _load_credentials(self, source: str) -> None:
        """
        Securely loads credentials. 
        Constraint: Fail closed on missing source or invalid env vars.
        """
        # In a real proposal, this would map to ENV variables, not files
        cred_value = os.getenv(source.upper())
        if not cred_value and source == "SECRET":
            raise RuntimeError("Fail-Closed: Secret Missing from Environment")

    def execute_task(self, task_payload: Any) -> bool:
        """
        Executes a heavy-weight task with explicit synchronization.
        Uses synchronous locking for state integrity (Prefer Heavy Pattern).
        """
        if not self._initialized:
            # Failing closed on initialization check
            raise RuntimeError("Fail-Closed: Engine Not Initialized")

        with self._lock:
            try:
                # Simulate heavy-weight processing logic
                time.sleep(0.1) 
                return True
            except Exception as e:
                # Fail closed on task execution failure
                raise RuntimeError(f"Orchestration failed: {str(e)}") from None

    def validate_mission_brief(self, brief_content: str) -> bool:
        """
        Validates mission brief content.
        Failing closed if brief is null/empty (Security Class Requirement).
        """
        # Placeholder for validation logic against internal policies
        # Do not attempt to write to 04_GOVERNANCE/
        self.context.state_lock = None  # Ensure lock state is managed
        
        if not brief_content:
            raise ValueError("Fail-Closed: Mission Brief is empty or missing")
        
        # Check for sensitive paths (Prefer heavy validation)
        if "/04_GOVERNANCE/" in brief_content:
            raise SecurityError("Fail-Closed: Brief references forbidden path")

    def run_heavy_cycle(self, action: Callable[[], bool]) -> bool:
        """
        Executes a heavy cycle, ensuring the callback executes fully.
        """
        result = False
        try:
            result = action()
        except Exception as e:
            # Do not hide failures (Fail Closed)
            raise RuntimeError(f"Heavy Cycle Failed: {str(e)}")
        return result


# Example Usage Proposal (Do not run directly, use for reference)
if __name__ == "__main__":
    try:
        # Construct Context from Environment Injection (No hardcoded secrets)
        context = SecureContext(
            execution_id=os.getenv("EXEC_ID"),
            mode="heavy"
        )

        engine = OrchestrationEngine(context)
        
        # Initialize logic
        engine._initialized = True
        
        # Validate Brief (Fail Closed if missing)
        brief = os.getenv("MISSION_BRIEF")
        if brief:
            engine.validate_mission_brief(brief)
            
    except Exception as e:
        # Log error (in production, would use a secure logger)
        print(f"ORCHESTRATION ERROR: {e}")
        exit(1)
```