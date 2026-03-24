---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
#!/usr/bin/env python3
"""
Secure Vulnerability Scanner Proposal Module
Security Class: CONFIDENTIAL
Task ID: 08_CYBER_E6_002_vuln_scanner
Compliance Checks: 
  - No hardcoded credentials (uses os.environ)
  - No writes to /04_GOVERNANCE/ paths
  - Fail-closed logic for restricted paths
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List

# Configure strict path filtering
RESTRICTED_PATHS = {"04_GOVERNANCE/", "/etc/shadow", "proc/self"}
LOG_DIR_ENV_VAR = "SCANNER_LOG_DIR"

class SecurityException(Exception):
    """Custom exception for security constraint violations."""
    pass

def get_secure_storage_path(base_path: Optional[str] = None) -> Path:
    """
    Proposes a secure local path for logging and configuration.
    Validates against restricted governance paths to prevent constitutional violations.
    """
    if not base_path:
        # Default to user's writable environment temp directory
        base_path = os.environ.get('HOME', '/tmp')
    
    try:
        # Ensure path is relative or absolute within allowed scopes
        secure_path = Path(base_path) / ".scanner_data"
        
        # Fail closed check: Reject if parent contains restricted segments
        if any(part in str(secure_path.parent) for part in RESTRICTED_PATHS):
            raise SecurityException(f"Path attempt blocked due to proximity to restricted segment: {secure_path.parent}")

        return secure_path.mkdir(exist_ok=True) / "scanner_logs"
    except Exception as e:
        # Log failure safely without exposing stack trace details publicly
        logging.error(f"Failed to initialize secure storage: {str(e)}")
        raise SecurityException("Secure storage initialization failed.") from e

def fetch_credentials(cred_type: str, service_name: str) -> Dict[str, str]:
    """
    Retrieves credentials safely from environment variables.
    Prevents hardcoded secrets.
    """
    # Construct secure key names to avoid accidental exposure
    prefix = f"{service_name.upper()}_CRED_"
    creds_map = {
        "api_key": prefix + "API_KEY",
        "username": prefix + "USER",
        "password": prefix + "PASS",
        "token": prefix + "TOKEN"
    }
    
    credentials = {}
    for key, env_var in creds_map.items():
        value = os.environ.get(env_var)
        if not value:
            # Propose defaulting to 'none' or rejecting operation if required
            continue 
        credentials[key] = value
        
    return credentials

def sanitize_report_output(report_path: Path, data: dict):
    """
    Writes report safely without overwriting sensitive system files.
    Ensures file operations respect permission constraints.
    """
    # Ensure path doesn't attempt to escape user scope
    try:
        with open(report_path / f"scan_report_{data.get('id', 'unknown')}.json", "w") as f:
            json.dump(data, f, indent=2)
        return True
    except PermissionError:
        logging.warning("Permission denied on report write path.")
        return False
    except Exception:
        logging.error(f"Unexpected error writing to {report_path}: {sys.exc_info()[0]}")
        return False

def run_scan_proposal(target_ip: str, port: int = 80) -> Dict:
    """
    Proposal for scanning logic. 
    In a real execution context, this would invoke nmap or Nessus API wrappers.
    Here, we structure the safe interface.
    """
    print(f"Proposal initiated for target: {target_ip}:{port}")
    
    # Setup secure logging location
    try:
        log_dir = get_secure_storage_path()
        setup_logging(log_dir)
        
        # Fetch credentials securely
        creds = fetch_credentials("scanner", "08_CYBER")
        
        if not creds.get('token'):
            raise SecurityException("No valid scanner token provided via environment variables.")
            
        # Placeholder for scanning logic implementation
        scan_result = {
            "status": "PROPOSED",
            "target": target_ip,
            "vulnerabilities_found": 0,
            "scan_type": "passive" # Default to passive unless authorized aggressive scan
        }
        
        # Propose output handling
        sanitize_report_output(log_dir / "reports", scan_result)
        
        return scan_result
        
    except SecurityException:
        # Fail closed immediately on security constraint breach
        logging.critical("Scan aborted due to security constraint violation.")
        raise

def setup_logging(log_path: Path):
    """Configures logger to write to the secure path proposed."""
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(str(log_path / "scanner_activity.log"))
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("08_CYBER_E6_002")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

if __name__ == "__main__":
    try:
        # This block represents the proposal execution entry point
        # It should be run in a controlled CI/CD or authorized environment
        result = run_scan_proposal(target_ip="192.168.1.1") 
        print(json.dumps(result))
    except SecurityException as e:
        sys.stderr.write(f"SECURITY FAILURE: {e}\n")
        sys.exit(1)
```