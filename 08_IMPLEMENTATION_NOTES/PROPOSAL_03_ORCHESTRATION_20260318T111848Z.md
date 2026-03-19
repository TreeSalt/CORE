---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import yaml
import pathlib
from typing import Dict, Any, List, Optional

def propose_domain_updates(config_path: str | None = None) -> Dict[str, Any]:
    """
    Proposes updates to the domains configuration file.
    
    This function safely processes the domains.yaml (if it exists),
    sets 'cruiser_model' to 'qwen3.5:9b' for every domain entry,
    and appends 'qwen3.5:9b' to the list of authorized_agents 
    if not already present.
    
    For safety and auditing, this function returns the proposed 
    configuration object (dict) rather than writing directly.
    To apply changes, return the dict and write it manually or 
    invoke a safe_write logic with explicit permission.
    """
    target_path = pathlib.Path(config_path) if config_path else None
    
    # Check if the domains file exists to process updates
    if not target_path or not target_path.exists():
        return {
            "status": "no_domains_file_found",
            "path": str(target_path),
            "proposed_model": "qwen3.5:9b"
        }

    try:
        # Read existing configuration safely
        with open(target_path, 'r') as f:
            domains = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {target_path}: {e}")
        return {"error": str(e)}

    # Handle different structure formats (dict or list)
    if isinstance(domains, dict):
        for domain_name, domain_config in domains.items():
            if isinstance(domain_config, dict):
                # Set the model for this domain entry
                domain_config['cruiser_model'] = 'qwen3.5:9b'
                
                # Initialize or retrieve authorized_agents list
                current_agents = domain_config.get('authorized_agents', [])
                # If it's not a list (edge case), convert to list
                if not isinstance(current_agents, list):
                    current_agents = [current_agents]
                
                # Append the model if not already in the list
                if 'qwen3.5:9b' not in current_agents:
                    current_agents.append('qwen3.5:9b')
                    
                domain_config['authorized_agents'] = current_agents
                
    elif isinstance(domains, list):
        # If domains is a list of configs (common for inventory)
        for entry in domains:
            if isinstance(entry, dict):
                entry['cruiser_model'] = 'qwen3.5:9b'
                current_agents = entry.get('authorized_agents', [])
                if not isinstance(current_agents, list):
                    current_agents = [current_agents]
                
                if 'qwen3.5:9b' not in current_agents:
                    current_agents.append('qwen3.5:9b')
                    
                entry['authorized_agents'] = current_agents

    return domains

# --- Safe Execution Logic ---
# 
# The following block demonstrates how to apply the updates if required.
# To strictly adhere to "No writes" during this interaction, it is commented out.
# Uncomment only when explicit authorization to write is given.

if __name__ == "__main__":
    import sys
    
    # 1. Determine config path (or default)
    config_path = sys.argv[1] if len(sys.argv) > 1 else "04_GOVERNANCE/DOMAINS.yaml"
    
    # 2. Generate the proposed configuration (No write yet)
    proposed_config = propose_domain_updates(config_path)
    
    # 3. Safety Check / Audit Log (Prints to console, no file write)
    if isinstance(proposed_config, dict) and 'error' not in proposed_config:
        print(f"Proposed updates generated for path: {config_path}")
        print(f"- Set 'cruiser_model' to 'qwen3.5:9b'")
        print(f"- Updated 'authorized_agents' lists.")
        
        # Uncomment the line below ONLY if you have explicit write permission:
        # import tempfile
        # with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.yaml') as tmp:
        #     yaml.dump(proposed_config, tmp)
        # print(f"Preview written to: {tmp.name}")
        
    elif isinstance(proposed_config, dict) and 'no_domains_file_found' in proposed_config:
        print("Domains file not found at specified path. Returning default proposal structure.")
```