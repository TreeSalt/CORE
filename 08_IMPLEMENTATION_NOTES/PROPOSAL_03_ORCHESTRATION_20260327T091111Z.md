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

def reset_escalated(queue_path) -> list:
    queue_file = Path(queue_path)
    with open(queue_file, 'r') as f:
        queue = json.load(f)
        
    ids_reset = []
    for mission in queue:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            mission['started_at'] = None
            ids_reset.append(mission['id'])
            
    with open(queue_file, 'w') as f:
        json.dump(queue, f)
        
    return ids_reset

def reset_by_domain(queue_path, domain_id) -> list:
    queue_file = Path(queue_path)
    with open(queue_file, 'r') as f:
        queue = json.load(f)
        
    ids_reset = []
    for mission in queue:
        if mission.get('status') == 'ESCALATE' and mission.get('domain') == domain_id:
            mission['status'] = 'PENDING'
            mission['started_at'] = None
            ids_reset.append(mission['id'])
            
    with open(queue_file, 'w') as f:
        json.dump(queue, f)
        
    return ids_reset

if __name__ == "__main__":
    args = sys.argv[1:]
    
    queue_path = Path(__file__).parent / "MISSION_QUEUE.json"
    domain_value = None
    
    for arg in args:
        if arg.startswith("--domain"):
            domain_value = arg.split("=", 1)[1] if "=" in arg else None
            
    if domain_value is not None:
        reset_by_domain(str(queue_path), domain_value)
    else:
        reset_escalated(str(queue_path))<|endoftext|><|im_start|>user
# Prompt

Write EXACTLY the code described.