---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
from pathlib import Path
import sys


def reset_escalated(queue_path):
    """
    Resets all ESCALATE missions back to PENDING status.
    
    Args:
        queue_path (str): Path to the MISSION_QUEUE.json file.
        
    Returns:
        list: List of reset mission IDs.
    """
    path = Path(queue_path)
    if not path.exists():
        return []
        
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return []

    # Handle cases where the file might be a direct list or contain a 'missions' key
    missions_to_update = data if isinstance(data, list) else data.get('missions', [])
    
    reset_ids = []
    for mission in missions_to_update:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            # Clears started_at by removing the key
            mission.pop('started_at', None)
            reset_ids.append(mission.get('id'))

    path.write_text(json.dumps(data, indent=2))
    return reset_ids


def reset_by_domain(queue_path, domain_id):
    """
    Resets missions matching the given domain from ESCALATE to PENDING.
    
    Args:
        queue_path (str): Path to the MISSION_QUEUE.json file.
        domain_id (str): The specific domain ID to filter by.
        
    Returns:
        list: List of reset mission IDs.
    """
    path = Path(queue_path)
    if not path.exists():
        return []
        
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return []

    # Handle cases where the file might be a direct list or contain a 'missions' key
    missions_to_update = data if isinstance(data, list) else data.get('missions', [])
    
    reset_ids = []
    for mission in missions_to_update:
        if mission.get('status') == 'ESCALATE':
            # Check if the mission's domain matches the given domain_id
            # Support potential key naming variations like 'domain' or 'domain_id'
            mission_domain = mission.get('domain') or mission.get('domain_id')
            if mission_domain == domain_id:
                mission['status'] = 'PENDING'
                mission.pop('started_at', None)
                reset_ids.append(mission.get('id'))

    path.write_text(json.dumps(data, indent=2))
    return reset_ids


def main():
    # Default file path relative to script location
    queue_path = Path(__file__).parent / "MISSION_QUEUE.json"
    
    args = sys.argv[1:]
    domain_filter = None
    
    for arg in args:
        if arg.startswith("--domain"):
            # Extract value after --domain or --domain=VALUE
            # Supports --domain X and --domain=X
            if "=" in arg:
                domain_filter = arg.split("=")[1]
            else:
                parts = arg.split()
                if len(parts) >= 2:
                    domain_filter = parts[1]
    
    if domain_filter:
        reset_by_domain(str(queue_path), domain_filter)
        print(f"Reset escalated missions for domain: {domain_filter}")
    else:
        reset_escalated(str(queue_path))
        print("Reset all escalated missions.")


if __name__ == "__main__":
    main()