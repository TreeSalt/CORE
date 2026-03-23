---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

class ReportingConstraintViolationError(Exception):
    """Raised when security or reporting constraints are violated."""
    pass

def _validate_path_safety(path: str) -> None:
    """
    Validates that a given path does not contain restricted domains.
    Constraint Enforced: No writes/reads to 04_GOVERNANCE/
    """
    forbidden_prefix = "04_GOVERNANCE/"
    
    if forbidden_prefix in path:
        raise ReportingConstraintViolationError(
            f"VIOLATION: Access attempt to restricted domain '{forbidden_prefix}'."
        )

def _validate_credentials_availability() -> None:
    """
    Validates that credentials are not hardcoded and are present in environment.
    Constraint Enforced: No hardcoded credentials (fail closed).
    """
    required_env_vars = ['REPORT_DB_HOST', 'REPORT_DB_USER', 'REPORT_DB_PASS']
    
    for var in required_env_vars:
        if not os.environ.get(var):
            raise ReportingConstraintViolationError(
                f"VIOLATION: Missing environment variable '{var}'. "
                "Hardcoded credentials are prohibited."
            )

class ReportVersionHistoryManager:
    """
    Secure manager for report version history.
    
    Security Class: INTERNAL
    Implements 'fail closed' logic on any constraint breach.
    """
    
    def __init__(self, storage_root: Optional[str] = None):
        # Determine storage root from environment or default to safe path
        self.storage_root = os.environ.get('REPORT_STORAGE_ROOT')
        if not self.storage_root:
            self.storage_root = "/var/reports"
        
        # Constraint Check 1: Domain Safety & Credential Availability
        _validate_path_safety(self.storage_root)
        _validate_credentials_availability()

    def log_version_change(self, report_id: str, version_info: Dict) -> None:
        """
        Logs a new version of a report.
        
        Constraints enforced:
        - Writes never target forbidden domains.
        - Credential validation is pre-required (done in __init__).
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        safe_filename = f"history_{report_id}_v{timestamp}.json"
        
        # Construct full path
        target_path = os.path.join(self.storage_root, "reports", report_id, safe_filename)
        
        # Constraint Check 2: Path Safety on Write (Defense in Depth)
        _validate_path_safety(target_path)
        
        # Actual write logic placeholder (uses validated session credentials)
        # with open(target_path, 'w') as f: ...

    def get_report_history(self, report_id: str) -> List[Dict]:
        """
        Retrieves the version history for a specific report.
        
        Constraints enforced:
        - Reads never target forbidden domains.
        """
        # Construct read path
        read_path = os.path.join(self.storage_root, "reports", report_id)
        
        # Constraint Check 2: Path Safety on Read (Defense in Depth)
        _validate_path_safety(read_path)
        
        return [] # Placeholder logic

if __name__ == "__main__":
    try:
        manager = ReportVersionHistoryManager()
        sample_version = {
            "report_id": "E4_005", 
            "version": 2.1,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        manager.log_version_change("E4_005", sample_version)
        
    except ReportingConstraintViolationError as e:
        sys.stderr.write(f"CRITICAL VIOLATION DETECTED: {e}\n")
        sys.exit(1)
```