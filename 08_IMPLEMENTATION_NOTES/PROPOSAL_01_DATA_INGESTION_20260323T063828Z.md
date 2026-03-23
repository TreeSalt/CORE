---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
import logging
from typing import Dict, Optional

# Security Configuration Constants (Do not hardcode values here)
CREDENTIAL_ENV_PREFIX = "CRYPTO_WS_"
SECRET_LOGGING_KEY = "API_SECRET"

def load_secure_config(env_prefix: str) -> Optional[Dict[str, str]]:
    """
    Load configuration from environment variables only.
    Fails closed if required variables are not set to ensure no default secrets are exposed.
    """
    config: Dict[str, str] = {}
    
    # Critical Check: Ensure we look for env vars that exist and are non-empty
    # This prevents accidentally loading empty strings or defaults that might leak context
    env_vars_to_check = ["API_KEY", "API_URL", "REGION"] 
    
    for var in env_vars_to_check:
        full_key = f"{env_prefix}{var}"
        value = os.environ.get(full_key)
        
        # If variable is not set or empty, return None to trigger fail-safe
        if value is None or value == "":
            return None
        
        config[var.lower()] = value

    return config

def log_secure(operation: str, context_data: Optional[Dict] = None):
    """
    Logging helper that ensures secrets are masked before writing to stdout/stderr.
    Prevents accidental leakage of sensitive data into logs.
    """
    if not logging.getLogger().isEnabledFor(logging.INFO):
        return
        
    # Mask any keys that look like secrets
    safe_context = {}
    if context_data:
        for k, v in context_data.items():
            if isinstance(v, str) and len(v) > 8: # Likely a key/token
                safe_context[k] = "***REDACTED***"
            else:
                safe_context[k] = v
                
    print(f"[SECURE_LOG] {operation}: {safe_context}")

def ingest_secure(data: Dict) -> Dict:
    """
    Simulates ingestion logic that uses credentials.
    Does NOT print or log raw secrets to stdout.
    """
    # Check configuration status (simulated)
    if not hasattr(ingest_secure, "_is_configured"):
        return {"status": "failed", "reason": "Configuration incomplete"}
        
    log_secure("Ingesting data batch", context_data={"count": 1}) # Context passed without sensitive keys
    
    return {
        "status": "success", 
        "processed_count": 1,
        "redacted_response": "**Data processed securely**"
    }

# Main Entry Point with Fail-Closed Logic
if __name__ == "__main__":
    try:
        # Load secure config. If it fails (missing env vars), script exits immediately.
        config = load_secure_config(CREDENTIAL_ENV_PREFIX)
        
        if not config:
            sys.stderr.write(f"FATAL: Missing configuration for {CREDENTIAL_ENV_PREFIX} environment variables.\n")
            sys.exit(1)

        # Simulate run
        result = ingest_secure({"sample": "payload"})
        print(json.dumps(result))
        
    except Exception as e:
        # Ensure no partial data is leaked on crash
        sys.stderr.write(f"FATAL: {str(e)}\n")
        sys.exit(1)
```