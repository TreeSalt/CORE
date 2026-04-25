---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import json
import sys
from pathlib import Path


def reset_escalated(queue_path):
    """Reads MISSION_QUEUE.json and resets all ESCALATE missions to PENDING status."""
    path = Path(queue_path)
    with open(path, 'r') as f:
        queue = json.load(f)
    
    if isinstance(queue, list):
        missions = queue
    elif isinstance(queue, dict) and 'missions' in queue:
        missions = queue.get('missions', [])
    else:
        return []
    
    reset_ids = []
    for mission in missions:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            mission['started_at'] = None
            reset_ids.append(mission['id'])
    
    with open(path, 'w') as f:
        json.dump(queue, f)
    
    return reset_ids


def reset_by_domain(queue_path, domain_id):
    """Reads MISSION_QUEUE.json and resets ESCALATE missions for the given domain to PENDING."""
    path = Path(queue_path)
    with open(path, 'r') as f:
        queue = json.load(f)
    
    if isinstance(queue, list):
        missions = queue
    elif isinstance(queue, dict) and 'missions' in queue:
        missions = queue.get('missions', [])
    else:
        return []
    
    reset_ids = []
    for mission in missions:
        if (mission.get('status') == 'ESCALATE' and 
            mission.get('domain_id') == domain_id):
            mission['status'] = 'PENDING'
            mission['started_at'] = None
            reset_ids.append(mission['id'])
    
    with open(path, 'w') as f:
        json.dump(queue, f)
    
    return reset_ids


def main():
    parser_args = sys.argv[1:]
    domain_id = None
    
    for arg in parser_args:
        if arg.startswith('--domain=') or arg.startswith('-d'):
            domain_id = arg.split('=')[1] if '=' in arg else arg[8:]
    
    script_path = Path(__file__).parent.parent / 'MISSION_QUEUE.json'
    queue_path = Path('MISSION_QUEUE.json').resolve()
    
    if domain_id:
        reset_ids = reset_by_domain(queue_path, domain_id)
    else:
        reset_ids = reset_escalated(queue_path)
    
    print(f"Reset {len(reset_ids)} mission(s): {reset_ids}")


if __name__ == '__main__':
    main()
```