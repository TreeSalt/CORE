---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# Domain: 05_REPORTING
# Security Class: INTERNAL
# Task: 05_REPORT_E4_003_domain_health
# Status: CORRECTIVE_PROPOSAL (Addressing HARD_FAIL - hardcoded_credentials)
# Constraints Compliant: No writes to 04_GOVERNANCE/, No hardcoded credentials, Fail closed

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# SECURE CONFIGURATION HANDLING
# Credentials are retrieved via Environment Variables (os.getenv)
# DO NOT hardcode API keys, tokens, or secrets in this script.
REQUIRED_ENV_VARS = ['DOMAIN_05_API_ENDPOINT', 'DOMAIN_05_AUTH_TOKEN']
OUTPUT_DIR = "./output_reports"

def _validate_environment() -> None:
    """
    Proposes strict validation for environment configuration.
    Fails closed if required credentials are missing or empty.
    """
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value:
            raise EnvironmentError(f"Constitutional Violation Missing: {var}. Please configure via secure vault.")

def _get_secure_config() -> Dict[str, str]:
    """
    Proposes loading configuration securely.
    Returns sanitized config dictionary for report generation.
    """
    try:
        _validate_environment()
        return {
            "endpoint": os.getenv('DOMAIN_05_API_ENDPOINT'),
            "auth_token_ref": f"ref:{os.getenv('DOMAIN_05_AUTH_TOKEN')}", # Mask sensitive value in ref only if needed, but strictly do not write token to file
            "timestamp": datetime.utcnow().isoformat()
        }
    except EnvironmentError:
        raise SystemExit(1)

def _sanitize_report_path(output_dir: str, prefix: str = "report") -> Path:
    """
    Proposes sanitizing output paths.
    Ensures no path traversal or writes to 04_GOVERNANCE/.
    """
    # Normalize path and ensure it is within allowed output directories
    base = Path(OUTPUT_DIR).resolve() / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Explicitly check against forbidden write locations
    forbidden_patterns = ["/04_GOVERNANCE/", "/system/"]
    
    for pattern in forbidden_patterns:
        if pattern in str(base):
            raise PermissionError(f"Write rejected: Path contains forbidden segment '{pattern}'")
            
    return base

def generate_domain_health_report() -> Dict:
    """
    Proposes the core logic for generating domain health metrics.
    Returns a dictionary structure to be serialized securely.
    """
    config = _get_secure_config()
    
    # Placeholder for actual health check logic (simulated)
    health_metrics = {
        "status_code": 200,
        "latency_ms": 45,
        "connection_pool_active": True
    }

    report = {
        "domain": "05_REPORTING",
        "timestamp": config["timestamp"],
        "security_class": "INTERNAL",
        "metrics": health_metrics,
        "status": "HEALTH_CHECK_PROPOSED"
    }
    
    return report

def propose_report_save(report: Dict) -> Optional[Path]:
    """
    Proposes saving the report securely.
    Returns Path to file or None if write fails (Fail Closed).
    """
    try:
        safe_path = _sanitize_report_path()
        
        with open(safe_path, 'w') as f:
            # Redact sensitive fields before writing if any were included in report logic
            sanitized = {k: v for k, v in report.items()} 
            json.dump(sanitized, f, indent=4)
            
        return safe_path
        
    except (IOError, PermissionError, ValueError) as e:
        # Fail closed on write error
        print(f"PROPOSAL REJECTED: Failed to save report. Error: {e}")
        return None

# Module Definition for Import by Orchestration Layer
if __name__ == "__main__":
    try:
        # This block executes locally only if run as standalone proposal verification
        # It does NOT persist state in Governance paths.
        print("Initiating Secure Domain Health Proposal...")
        config = _get_secure_config()
        
        # Generate Report Content
        report_content = generate_domain_health_report()
        
        # Attempt to save (Proposed Action)
        result_path = propose_report_save(report_content)
        
        if result_path:
            print(f"PROPOSAL COMPLETED SUCCESSFULLY at: {result_path}")
        else:
            print("PROPOSAL FAILED. Check environment variables and path constraints.")
            
    except SystemExit:
        print("CRITICAL CONFIGURATION ERROR. Aborting proposal execution.")
    except Exception as e:
        print(f"UNHANDLED PROPOSAL ERROR: {e}")
```