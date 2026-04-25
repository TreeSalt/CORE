---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import json
import pathlib
import sys


def reset_escalated(queue_path):
    queue_file = pathlib.Path(queue_path)
    with open(queue_file) as f:
        missions = json.load(f)
    
    reset_ids = []
    for mission in missions:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])
    
    with open(queue_file, 'w') as f:
        json.dump(missions, f, indent=2)
    
    return reset_ids


def reset_by_domain(queue_path, domain_id):
    queue_file = pathlib.Path(queue_path)
    with open(queue_file) as f:
        missions = json.load(f)
    
    reset_ids = []
    for mission in missions:
        if (mission.get('status') == 'ESCALATE' and 
            mission.get('domain') == domain_id):
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])
    
    with open(queue_file, 'w') as f:
        json.dump(missions, f, indent=2)
    
    return reset_ids


if __name__ == '__main__':
    queue_path = pathlib.Path.cwd() / 'MISSION_QUEUE.json'
    domain_arg = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--domain=') or arg.startswith('--domain'):
            domain_arg = arg.split('=', 1)[1] if '=' in arg else arg.split('=')[1]
    
    if domain_arg:
        result = reset_by_domain(str(queue_path), domain_arg)
    else:
        result = reset_escalated(str(queue_path))
    
    print(f"Reset {len(result)} mission(s): {result}")
```