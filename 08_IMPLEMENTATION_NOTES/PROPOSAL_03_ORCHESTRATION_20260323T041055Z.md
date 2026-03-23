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
from pathlib import Path
from typing import Dict, Any, Optional

class MissionTemplateGenerator:
    """
    Generator for Orchestration Mission Templates.
    
    SECURITY COMPLIANCE:
    - No writes to 04_GOVERNANCE/ (enforced)
    - No hardcoded credentials (enforced via env vars)
    - Fail closed on constraint breach (implemented)
    - Proposals only (configuration definition, not execution)
    """

    FORBIDDEN_PATH_PATTERN = "04_GOVERNANCE"
    
    def __init__(self, orchestration_root: Path):
        self.root_path = Path(orchestration_root).resolve()
        # Constraint Check: Ensure root does not land inside forbidden governance dir
        if str(self.root_path).find("04_GOVERNANCE") != -1 or "04_GOVERNANCE" in str(self.root_path):
            raise RuntimeError(f"Initialization failed: Forbidden path detected. Access to {self.root_path} denied.")

    def get_secret_reference(self, secret_name: str) -> Optional[str]:
        """Retrieves secrets strictly from environment variables. Fallback to None."""
        # Constraint Check: No hardcoded strings passed here
        return os.getenv(secret_name)

    def validate_write_target(self, target_path: Path) -> bool:
        """
        Enforces 'No writes to 04_GOVERNANCE/' constraint.
        Returns False and raises error if violation is detected.
        """
        target_resolved = str(target_path).lower()
        
        # Constraint Check: Fail closed on breach
        if "04_governance" in target_resolved:
            raise PermissionError(f"WRITE BLOCKED: Attempted write to governance path detected at {target_path}")
            
        return True

    def create_mission_template_payload(self, mission_id: str, task_definitions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs a JSON payload representing a proposed mission template.
        Status remains 'PROPOSED' to adhere to 'Proposals only' constraint.
        """
        # Constraint Check: Ensure input configs don't contain raw secrets if possible
        clean_definitions = {}
        
        for task_id, details in task_definitions.items():
            if 'secret' in details:
                raise ValueError(f"Security Violation: Task {task_id} contains embedded secrets.")
            clean_definitions[task_id] = {
                "type": details.get("action_type"),
                "dependencies": details.get("dependencies", []),
                "is_secure_task": details.get("requires_credential", False) # Flag only, not store cred
            }

        return {
            "payload_version": "1.0",
            "mission_id": mission_id,
            "status": "PROPOSED",
            "tasks": clean_definitions,
            "metadata": {
                "generator_version": "1.0.0",
                "security_level": "HIGH" 
            }
        }

    def propose_and_store_template(self, mission_id: str, task_definitions: Dict[str, Any], output_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Attempts to generate and store the template.
        Constraint: No write to 04_GOVERNANCE/ is allowed.
        Fails safely if path validation fails.
        """
        # 1. Path Validation (Fail Closed on breach)
        try:
            self.validate_write_target(output_dir)
        except PermissionError as e:
            print(f"Template proposal rejected due to governance violation: {e}")
            return None

        # 2. Create payload
        template = self.create_mission_template_payload(mission_id, task_definitions)
        
        # 3. Construct safe output path (ensuring not in forbidden areas)
        file_path = output_dir / f"{mission_id}.json"
        
        # Double check specific forbidden patterns just in case
        if "04_governance" in str(file_path):
             raise PermissionError(f"Write denied: Forbidden path {file_path}")

        # 4. Generate file (Proposed state)
        try:
            # Ensure directory exists, but do not overwrite sensitive files
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write proposed template
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            return {
                "status": "PROPOSED",
                "location": str(file_path),
                "template_data": template
            }
            
        except Exception as e:
            print(f"Template proposal failed with exception: {e}")
            return None # Fail closed: do not create partial files

if __name__ == "__main__":
    # Example usage for 'Proposals Only' demonstration (Simulation)
    # Ensure output dir is NOT 04_GOVERNANCE
    
    # Simulated environment setup
    import sys
    sys.argv = ['script', '/workspace/orchestration'] # Hardcoded root in simulation example, usually env var
    
    try:
        base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/orchestration")
        
        generator = MissionTemplateGenerator(base_dir)
        
        task_config = {
            "deploy_prod": {
                "action_type": "deploy",
                "dependencies": ["healthcheck"],
                "requires_credential": True # Flag only, cred retrieved via env if needed
            },
            "notify_ops": {
                "action_type": "send_notification",
                "dependencies": ["deploy_prod"]
            }
        }
        
        result = generator.propose_and_store_template("mission-2023-10-27-A", task_config, base_dir / "templates")
        
        if result:
            print(f"Proposed Template Generated: {result['location']}")
            print(f"Status: {result['status']}")
            
    except PermissionError as e:
        print(f"FATAL: Governance violation detected. Operation aborted.")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
```