---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# SECURITY CLASSIFICATION: INTERNAL
# DOMAIN: 03_ORCHESTRATION
# TASK ID: 03_ORCH_E7_005_health_check (Proposal/Design)

# ==============================================================================
# CONSTRAINT COMPLIANCE MODULE
# ==============================================================================
# 1. No writes to 04_GOVERNANCE/
# 2. No hardcoded credentials
# 3. Fail closed on constraint breach
# 4. Output valid Python code only
# ==============================================================================

class OrchestrationHealthCheck:
    """
    Health Check Utility for Orchestration Systems.
    
    DESIGN PRINCIPLES (Proposed):
    - Uses environment variables for configuration to avoid hardcoding credentials.
    - Strict path validation to prevent writes to 04_GOVERNANCE/.
    - Implements 'Fail Closed' logic: returns False/Error on any health check failure.
    """

    # Paths forbidden by security policy
    FORBIDDEN_PATHS = ["/04_GOVERNANCE/", "/secrets/", "/admin/"]
    
    # Safe default log directory (must be writable)
    DEFAULT_LOG_DIR = "/tmp/orch_health_logs"
    
    class HealthError(Exception):
        """Base exception for health check failures."""
        pass

    def __init__(self, config_path: Optional[str] = None):
        self.config: Dict[str, Any] = {}
        self.enabled: bool = True
        self._validate_config_path(config_path)
        self._load_safe_config()

    def _validate_config_path(self, path: Optional[str]) -> None:
        """Ensure config path does not target forbidden directories."""
        if path and any(fp in path for fp in self.FORBIDDEN_PATHS):
            raise self.HealthError(f"Constraint Breach: Path '{path}' contains forbidden segment.")

    def _load_safe_config(self) -> None:
        """Load configuration from environment or safe file location only."""
        # Prioritize Environment Variables to prevent hardcoded secrets
        self.config['endpoint'] = os.getenv("ORCH_HEALTH_ENDPOINT", "http://localhost:8080/health")
        self.config['timeout'] = int(os.getenv("ORCH_HEALTH_TIMEOUT", "5"))
        
        # If a path is provided and safe, use it; otherwise default config
        if self.config.get('_override_path'):
            path = self.config.pop('_override_path')
        elif config_path:
             # Double check forbidden paths on user input
            path = config_path
            for fp in self.FORBIDDEN_PATHS:
                if fp in path:
                    raise self.HealthError(f"Security Violation: Forbidden path segment '{fp}' detected.")
            
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    try:
                        json.load(f)
                        # Load config
                        self.config.update(json.load(f))
                    except (json.JSONDecodeError, IOError) as e:
                        raise ValueError("Config file invalid or unreadable")
        
        # Ensure timeout is within safe limits
        if 'timeout' not in self.config:
            self.config['timeout'] = 5
            
    def _log_error_internal(self, message: str) -> None:
        """Log errors to a safe location (/tmp) without writing to 04_GOVERNANCE/."""
        log_dir = os.getenv("LOG_DIR", self.DEFAULT_LOG_DIR)
        
        # Failsafe check: Ensure we are not in a governance write scope
        if any("/04_GOVERNANCE/" in path for path in [log_dir]):
            raise RuntimeError(f"Critical Security Error: Logging intercepted. Cannot access {log_dir}")

        if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
            try:
                with open(os.path.join(log_dir, "health_errors.log"), 'a') as f:
                    f.write(f"[{datetime.now()}] ERROR: {message}\n")
            except PermissionError:
                 raise RuntimeError("Log directory not writable. Fail Closed.")
        else:
             # Create in safe temp if main dir unavailable (fallback only)
             fd = os.open(os.path.join("/tmp", f"health_err_{datetime.now().timestamp()}.log"), 
                          os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
             with os.fdopen(fd, 'w') as f:
                 f.write(f"[{datetime.now()}] ERROR: {message}\n")

    def _check_connection(self, url: str) -> bool:
        """Attempt HTTP connection. Fail closed on timeout or error."""
        try:
            req = urllib.request.Request(url, method='GET')
            # Add headers if needed (avoid leaking auth in GET for simple health check)
            with urllib.request.urlopen(req, timeout=float(self.config.get('timeout', 5))) as response:
                return response.status == 200
        except urllib.error.URLError as e:
            # Log the error securely
            self._log_error_internal(f"Connectivity failed for {url}: {str(e)}")
            return False
        except Exception as e:
             # Fail closed on unexpected errors
             self._log_error_internal(f"Unexpected error during health check: {type(e).__name__}")
             return False

    def run_health_check(self) -> Dict[str, Any]:
        """Execute the full health check sequence. Returns status dict."""
        if not self.enabled:
            raise ValueError("HealthCheck disabled by configuration.")
        
        # Validate that we are not leaking sensitive data (e.g. printing secrets)
        if os.getenv("ADMIN_SECRET"):
            raise ValueError("Configuration Error: Sensitive environment variable ADMIN_SECRET detected.")

        endpoint = self.config.get('endpoint')
        
        if not endpoint:
             raise ConfigurationError("Health Endpoint not configured in Environment or Config file.")

        # Perform checks with fail-closed logic
        is_healthy = self._check_connection(endpoint)
        
        result = {
            "status": "HEALTHY" if is_healthy else "UNHEALTHY",
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }

        # Component checks
        ping_url = f"{endpoint}/ping" if endpoint.endswith('/') else f"{endpoint}/ping"
        try:
            # Simulated component check (would call specific endpoints in real code)
            if self._check_connection(ping_url):
                result["components"]["connectivity"] = "OK"
            else:
                result["components"]["connectivity"] = "FAILED"
                
            # Logic to verify database connection or other DBs would go here
            # We ensure we don't read credentials from disk during this process
        except Exception as e:
            self._log_error_internal(f"Component check failed: {e}")
            result["status"] = "UNHEALTHY"

        if not is_healthy:
             self._log_error_internal("Orchestration health check failed.")
        
        return result

    def reset(self) -> None:
        """Reset instance state for testing."""
        self.enabled = False
        self.config = {}

# Configuration Error Class Definition (Internal use)
class ConfigurationError(Exception):
    pass

if __name__ == "__main__":
    # Proposal Only - Example Usage / Mock Execution Path
    try:
        hc = OrchestrationHealthCheck()
        status = hc.run_health_check()
        print(f"Health Status: {status}")
    except Exception as e:
        print(f"Proposed Implementation Error: {e}")
```