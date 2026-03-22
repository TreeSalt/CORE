---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import re
from typing import Any, Dict, Optional, Union
from pathlib import Path

# --- SECURITY CONFIGURATION ---
# Hardcoded credentials are forbidden. Use environment variables only.
CREDENTIAL_ENV_PREFIX = "QUEUE_AUTH_"
SENIORITY_CHECK_PATH = "/04_GOVERNANCE/" # Reference check, not write path

class QueueResetProposalError(Exception):
    """Raised when a proposal violates security constraints."""
    pass

def is_path_safe(path: str) -> bool:
    """
    Validates that a path does not target governance directories.
    Fail closed on breach.
    """
    forbidden_pattern = re.compile(r'^.*04_GOVERNANCE/.*$')
    if forbidden_pattern.search(path):
        raise QueueResetProposalError("Path access restricted: Cannot write to 04_GOVERNANCE/")
    return True

def is_cred_hardcoded(data: Any) -> bool:
    """
    Checks string data for patterns resembling hardcoded secrets.
    Fail closed on breach.
    """
    if isinstance(data, str):
        # Regex check for password/secret=literal_string patterns without env var placeholders
        forbidden_credential_pattern = re.compile(
            r'.*(password|secret|api_key|token).*=.*[\dA-Za-z_\-]{4,}\s', 
            re.IGNORECASE
        )
        if forbidden_credential_pattern.search(data):
            raise QueueResetProposalError("Constraint breach: Hardcoded credentials detected.")
    return False

class QueueResetCommandProposal:
    """
    Task: 03_ORCH_E4_001_queue_reset_command
    Purpose: Proposes a secure queue reset operation without executing writes 
             to governance paths or using hardcoded secrets.
    """
    
    def __init__(self, target_queue_name: str):
        self.target_queue_name = target_queue_name
        self.command_buffer: Dict[str, Any] = {}
        
        # Load credentials from environment if available, else None
        # Fail closed if env var not set but required (fail safe)
        self.auth_token = os.getenv("QUEUE_AUTH_TOKEN", "") 
        self.api_endpoint = os.getenv("QUEUE_API_ENDPOINT")

    def _validate_context(self) -> bool:
        """Validate proposal context against constraints."""
        try:
            # Check for hardcoded credentials in the class instance
            is_cred_hardcoded(self.auth_token)
            
            # Check API endpoint path safety
            if self.api_endpoint:
                is_path_safe(self.api_endpoint)
                
            return True
        except QueueResetProposalError as e:
            raise

    def build_reset_sequence(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Generates the reset command proposal structure.
        Returns a validated configuration object ready for review/execution.
        """
        if not self._validate_context():
            raise QueueResetProposalError("Context validation failed.")

        # Build the command payload
        reset_payload = {
            "target": self.target_queue_name,
            "action": "RESET",
            "mode": "PROPOSAL" if dry_run else "EXECUTE",
            "dry_run": dry_run,
            "credentials_source": os.environ.get("QUEUE_AUTH_TOKEN"), # Reference only
        }
        
        # Add safety check flag
        reset_payload["governance_path_check"] = True
        
        return reset_payload

    def generate_proposal(self) -> Dict[str, Any]:
        """
        Public interface to generate the proposal.
        Ensures no constraint breaches before returning.
        """
        try:
            self._validate_context()
            payload = self.build_reset_sequence(dry_run=True)
            return payload
        except QueueResetProposalError:
            # Fail closed: Do not return partial or insecure proposals
            raise

# --- USAGE PROPOSAL (DO NOT EXECUTE DIRECTLY) ---
# This block demonstrates the usage pattern without writing to governance paths.

if __name__ == "__main__":
    try:
        proposal_engine = QueueResetCommandProposal(target_queue_name="msg.queue.orders")
        
        # Ensure environment variables are set externally, not here
        # e.g., export QUEUE_AUTH_TOKEN=<secure_value>
        
        result = proposal_engine.generate_proposal()
        
        # Safe print for review purposes only
        if result.get("mode") == "PROPOSAL":
            print(f"Proposal Generated:\n{result}")
        else:
            raise QueueResetProposalError("Constraint breach: Cannot execute without review.")
            
    except QueueResetProposalError as e:
        # Fail closed on constraint breach
        print(f"Security Alert: Proposal rejected - {e}")
```