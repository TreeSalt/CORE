---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import logging
from pathlib import Path

# Configuration for security validation (No hardcoded credentials)
CONFIG = {
    'env_path': os.environ.get('BENCHMARK_ENV_PATH', None),
    'allowed_paths': ['valid_data/', 'output_logs/'],
    'restricted_dirs': ['04_GOVERNANCE/']
}

logger = logging.getLogger(__name__)

class PreflightTestRunner:
    def __init__(self):
        """Initialize preflight test runner without hardcoded credentials."""
        self.credentials_validated = False

    def validate_credentials(self):
        """Validate environment variables instead of hardcoding secrets."""
        try:
            # Check for API_KEY or similar from OS env
            api_key = os.environ.get('BENCHMARK_API_KEY')
            if not api_key or 'hardcoded' in api_key.lower():
                raise ValueError("Invalid credentials configuration detected")
            self.credentials_validated = True
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            raise

    def check_path_access(self, target_path: str):
        """Ensure no writes occur to restricted directories."""
        # Fail closed if path matches restricted list
        if '04_GOVERNANCE' in target_path.lower():
            raise PermissionError(f"Access denied: Write to {target_path} violates policy 04_GOVERNANCE")

    def validate_environment(self):
        """Run preflight checks."""
        self.validate_credentials()

        # Simulating path check logic without actual file writes
        if CONFIG['env_path']:
            target = Path(CONFIG['env_path'])
            # Verify directory is in allowed list or restricted list
            if str(target).endswith(self.allowed_paths[0]) and not str(target).startswith("04_GOVERNANCE/"):
                logger.info("Path check passed.")
            else:
                raise ValueError(f"Environment path validation failed: {CONFIG['env_path']}")

def run_preflight_test():
    runner = PreflightTestRunner()
    try:
        runner.validate_environment()
        # Additional checks could go here
        return {"status": "PASSED", "checks_complete": True}
    except (ValueError, PermissionError) as e:
        logger.critical(f"Preflight test failed due to constraint breach: {e}")
        return {"status": "FAILED", "breach_reason": str(e)}

# Example execution (Not executed here per 'Proposals only' constraint)
# if __name__ == "__main__":
#     result = run_preflight_test()
#     print(result)
```