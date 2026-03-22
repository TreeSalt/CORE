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
from typing import Optional

class OrchSecurityError(Exception):
    """Custom exception for constraint breaches."""
    pass

# --- CONSTRAINT HANDLING MODULE ---

class OrchGovernancePath:
    # Forbidden segments that should never be touched or referenced in file paths
    FORBIDDEN_SEGMENTS = ["/04_GOVERNANCE/", "\\04_GOVERNANCE\\", "/gov", "admin/"] 

    @staticmethod
    def check_path(path: str) -> bool:
        """Validates if a path is safe. Raises PermissionError if forbidden."""
        for seg in OrchGovernancePath.FORBIDDEN_SEGMENTS:
            if seg in path:
                raise PermissionError(f"Access denied: Forbidden segment '{seg}' found in path.")
        return True

# --- TASK IMPLEMENTATION ---

def generate_mantis_readme_proposal() -> Optional[str]:
    """
    Generates a proposal artifact for task 03_ORCH_E3_002_mantis_readme.
    
    Constraints:
    - Proposals only (returns string, no file write).
    - No writes to /04_GOVERNANCE/.
    - No hardcoded credentials.
    - Fail closed on breach.
    """
    
    # Define the template content
    # Using f-strings carefully to ensure no secrets leak
    readme_template = f"""# Mantis Orchestration Integration README

## 1. Overview
This document defines the orchestration requirements for interfacing with Mantis issue trackers.
All credentials must be managed externally via secure secrets stores.

## 2. Configuration Environment Variables
The following variables MUST be populated in the environment (DO NOT HARDCODE):
- `MANTIS_API_URL`: Base URL of the Mantis instance (e.g., https://mantis.company.internal)
- `MANTIS_AUTH_TOKEN`: API token for authentication. Fetch from Vault/Secrets Manager.
- `TASK_ORCHE_ID`: `03_ORCH_E3_002_mantis_readme`

## 3. Security Compliance
- **Path Restrictions**: Output logs and artifacts must not write to `/04_GOVERNANCE/`.
- **Credential Handling**: All authentication tokens are injected at runtime via environment variables.
- **Secret Rotation**: Credentials are assumed ephemeral; implement rotation policies in orchestration config.

## 4. Deployment Proposal
1. Deploy configuration files to the `deploy-configs` volume (not governance).
2. Inject secrets using `kubernetes-secrets-provider` or equivalent.
3. Verify connection health check endpoint before job scheduling."""

    # --- CONSTRAINT VALIDATION ---
    
    # Check for forbidden path references in content (guard rail)
    if "/04_GOVERNANCE/" in readme_template:
        raise OrchSecurityError("Generated content contains forbidden path references.")
    
    # Check for hardcoded credential patterns (sanitization check)
    secret_patterns = [
        r'password\s*[=]\s*["\']?\w+["\']?', 
        r'api_key\s*[=]\s*["\']?live', 
        r'secret_token\s*[=]\s*["\']?\d{3,}',
        r'access_key\s*[=]\s*["\']?[0-9a-f]{10,}'
    ]
    
    for pattern in secret_patterns:
        if re.search(pattern, readme_template):
            raise OrchSecurityError("Generated content contains hardcoded credential patterns.")

    # Ensure no actual write operations occur (Fail closed on breach simulation)
    # In a real orchestration system, this would trigger an audit event.
    return readme_template

if __name__ == "__main__":
    try:
        print(f"Generating proposal for task 03_ORCH_E3_002_mantis_readme...")
        
        # Attempt generation (No file writes performed)
        content = generate_mantis_readme_proposal()
        
        if content:
            print("--- PROPOSAL CONTENT ---")
            print(content)
            print("Proposal generated successfully.")
        else:
            print("No proposal to return.")
            
    except PermissionError as e:
        # Fail closed on permission breach
        print(f"[FATAL] {e}")
        print("Action: Terminating orchestration task.")
    except OrchSecurityError as e:
        # Fail closed on security breach
        print(f"[FATAL] {e}")
        print("Action: Terminating orchestration task.")
        
    print("--- END OF PROCESS ---")
```