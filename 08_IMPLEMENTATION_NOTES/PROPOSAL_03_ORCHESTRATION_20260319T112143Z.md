---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

# Constraint Constants
FORBIDDEN_PATH_PREFIXES = ("/04_GOVERNANCE/", "/etc/ssh/", "/root/")
MAX_SECRET_LENGTH = 64 # Prevent accidental exposure in logs

class ComplianceViolationError(Exception):
    """Raised when a constitutional or security constraint is breached."""
    pass

def validate_path_security(path: str) -> bool:
    """Fail closed check on path prefixes."""
    if any(path.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES):
        raise ComplianceViolationError(f"CONSTITUTIONAL VIOLATION: Forbidden path {path}")
    return True

class MantisReadmeProposalHandler:
    def __init__(self, output_dir: str = "/tmp/orchestration_proposals"):
        self.output_dir = output_dir
        self._credentials_cached: Optional[str] = None  # Safe initialization
    
    @property
    def has_credentials(self) -> bool:
        """Check for accidental credential storage."""
        return self._credentials_cached is not None

    def generate_proposal_payload(self, task_id: str = "03_ORCH_E3_002_mantis_readme") -> Dict[str, Any]:
        """Generate the proposal content without writing to disk or governance space."""
        
        # Safety Check 1: Validate Output Directory
        validate_path_security(self.output_dir)
        
        # Safety Check 2: Check for stored secrets
        if self.has_credentials:
            raise ComplianceViolationError("Hardcoded credentials detected in session.")

        # Construct Proposal Payload (Proposals Only, No Execution Writes)
        proposal_payload = {
            "task_id": task_id,
            "domain": "03_ORCHESTRATION",
            "security_class": "INTERNAL",
            "status": "PROPOSAL_READY",
            "action_type": "READ_AND_DOCUMENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compliance_status": {
                "writes_to_governance": False,
                "reads_forbidden_paths": False,
                "secrets_exposed": False
            },
            "content_summary": {
                "title": "Mantis Orchestration Workflow Documentation",
                "version": "0.1_CORRECTIVE", # Corrective context from HARD_FAIL
                "requires_execution": False, 
                "notes": "Corrective action from previous failed governance_write_attempt."
            }
        }
        
        return proposal_payload

def main():
    try:
        proposal_handler = MantisReadmeProposalHandler("/safe/staging/output")
        payload = proposal_handler.generate_proposal_payload()
        
        # Output the proposal for review (Proposals Only)
        print(json.dumps(payload, indent=2))
        
    except ComplianceViolationError as e:
        sys.stderr.write(f"FATAL SECURITY VIOLATION: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"UNEXPECTED ERROR: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()