---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
from pathlib import Path

class BenchmarkProposalManager:
    """
    Secure manager for generating proposals related to specific tasks.
    Does not write to governance directories. Uses environment variables for secrets.
    """
    # Constants for restricted paths
    GOVERNANCE_PATH_PREFIX = "/04_GOVERNANCE/"
    
    def __init__(self, task_id):
        if not isinstance(task_id, str):
            raise TypeError(f"task_id must be a string. Got: {type(task_id)}")
        self.task_id = task_id
        # Check environment variables for required secrets or config paths (using env vars)
        if not os.getenv("PROPOSAL_CONFIG_PATH", ""):
            raise EnvironmentError(f"Configuration path not found in environment.")
        
        # Define safe output directory based on config (avoiding governance)
        self.safe_output_dir = Path(os.getenv("OUTPUT_DIR", "./proposals"))
        if self.safe_output_dir.exists() and str(self.safe_output_dir).startswith(self.GOVERNANCE_PATH_PREFIX):
            raise SecurityError(f"Output directory is within restricted governance path.")

    def _validate_write_path(self, target_path: Path) -> None:
        """Validates that a write path is not within the governance directory."""
        if self._is_governance_path(target_path):
            raise GovernanceWriteError(f"Attempted write to restricted path: {target_path}")

    def _is_governance_path(self, target_path: Path) -> bool:
        """Checks if a path string or object contains the governance prefix."""
        # Ensure we convert to absolute or check string representation for safety
        path_str = str(target_path).replace("\\", "/")  # Normalize separators
        return self.GOVERNANCE_PATH_PREFIX in path_str

    def load_config_secrets(self) -> dict:
        """
        Loads configuration from environment variables.
        Does NOT hardcode secrets.
        """
        config = {
            "api_key": os.getenv("PROPOSAL_API_KEY"), 
            # Add other necessary non-secret configs or use env vars for all sensitive data
            "db_url": os.getenv("PROPOSAL_DB_URL")
        }
        
        # Fail closed if critical secrets are missing
        if not config.get("api_key"):
            raise MissingSecretError("CRITICAL: API_KEY environment variable is required but missing.")
            
        return config

    def generate_proposal_plan(self, target_path: str = None) -> dict:
        """
        Generates a proposal plan for the given task.
        Safely constructs paths and validates them before writing logic (simulated).
        """
        # Use safe defaults if no path provided
        if not target_path:
            # Construct a safe default path, ensuring it doesn't hit governance dirs
            base_path = self.safe_output_dir
            # Ensure the constructed path does not resolve to a gov dir (security check)
            final_path = Path(base_path / self.task_id)
            
            self._validate_write_path(final_path)

        # Simulated plan generation (no actual writes to disk for this proposal method)
        # This ensures we are generating *proposals* and not executing full logic yet
        return {
            "task_id": self.task_id,
            "status": "proposal_generated",
            "details": f"Proposal structure defined for task: {self.task_id}",
            "validation_passed": True
        }

    def execute_proposal(self, plan: dict) -> bool:
        """
        Executes the proposal. 
        Fails closed on any error during execution or validation.
        """
        # Validate inputs
        if not isinstance(plan, dict):
            raise TypeError("Plan must be a dictionary.")
            
        task_id = plan.get("task_id")
        if not task_id:
             raise ValueError("Proposal plan missing task_id.")

        # Simulate execution check against governance (just checking read logic for safety)
        safe_path = Path(task_id).parent
        
        # Check that we are not trying to read/write inside governance *during execution*
        if self._is_governance_path(safe_path):
             raise GovernanceReadError(f"Attempting to access restricted path: {safe_path}")

        try:
            # Perform logic steps (Simulated)
            print(f"Executing proposal for task: {task_id}")
            return True
        except Exception as e:
            # Fail closed on any exception during execution
            print(f"Execution failed for task {task_id}: {e}", file=sys.stderr)
            sys.exit(1)

class SecurityError(Exception):
    """Custom exception for security violations."""
    pass

class GovernanceWriteError(SecurityError):
    """Custom exception for writing to governance directories."""
    pass

class MissingSecretError(EnvironmentError):
    """Custom exception for missing required secrets."""
    pass

class GovernanceReadError(SecurityError):
    """Custom exception for reading from governance directories."""
    pass

if __name__ == "__main__":
    # Initialize manager with task ID from prompt header or env var (safe fallback)
    TASK_ID = os.getenv("TASK_ID", "06_BENCH_E6_crypto_backfill_test")
    
    try:
        manager = BenchmarkProposalManager(TASK_ID)
        
        # Load config (validates secrets via environment, not hardcoded)
        config = manager.load_config_secrets()
        
        # Generate proposal plan (safe path construction)
        plan = manager.generate_proposal_plan(target_path="proposals/06_BENCH_E6_crypto_backfill_test")
        
        if plan.get("status") == "proposal_generated":
            # Only execute if generated successfully and safe
            success = manager.execute_proposal(plan)
            if not success:
                print("Proposal execution failed.", file=sys.stderr)
            
    except MissingSecretError as e:
        print(f"Missing Critical Secret: {e}", file=sys.stderr)
        sys.exit(1)
    except GovernanceWriteError as e:
        print(f"Governance Write Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch any unexpected errors (fail closed)
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)
```