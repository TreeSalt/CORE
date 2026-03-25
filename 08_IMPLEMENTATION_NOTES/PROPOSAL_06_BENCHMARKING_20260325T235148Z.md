---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

# 06_BENCH_E8_002_prompt_test // Proposals Only

```python
class BenchmarkTaskExecutor:
    """
    SECURE TASK PROPOSAL STRUCTURE
    CONSTRAINTS:
      - No writes to 04_GOVERNANCE/ (simulated safety check)
      - No hardcoded credentials
      - Proposals only (no execution)
    """

    def __init__(self, task_id="06_BENCH_E8_002_prompt_test"):
        self.task_id = task_id
        self.status = "AWAITING_MISEON_BRIEF"
        
    def initialize(self):
        """Validates constraints before proceeding."""
        # Constraint Check: No Credentials in Config
        if hasattr(self, 'credentials'):
            raise SecurityError("Hardcoded credentials detected.")
            
        # Constraint Check: Directory Access Control
        self.allowed_paths = ["/safe", "/data"]
        forbidden = ["/04_GOVERNANCE/"]
        
        if any(path.startswith("/04") for path in self.allowed_paths):
            self._abort("Violation of no writes to 04_GOVERNANCE/")
            
    def process_request(self, brief_content):
        """Processes mission brief safely."""
        if not brief_content:
            raise ValueError("Mission Brief is required to continue task.")
            
        # Fail closed on missing input
        return self.status
    
    def _abort(self, reason):
        """Handles constraint violations by halting state transition."""
        print(f"HALT: {reason}")
        self.status = "TERMINATED"

# Security Check Implementation
import sys
from io import StringIO

class SecurityError(Exception):
    pass

if __name__ == "__main__":
    executor = BenchmarkTaskExecutor(task_id="06_BENCH_E8_002_prompt_test")
    # Proposing readiness until brief is provided via input() or API call
    print(f"Task Ready. Awaiting valid Python code or Brief...")
```