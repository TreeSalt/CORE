---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
import pathlib
import sys


def reset_escalated(queue_path):
    """Reset status of all escalated missions to PENDING."""
    path = pathlib.Path(queue_path)
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        queue_data = json.load(f)

    missions = queue_data.get('missions', []) or []
    reset_ids = []

    for mission in missions:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(queue_data, f)

    return reset_ids


def reset_by_domain(queue_path, domain_id):
    """Reset status of escalated missions for a specific domain."""
    path = pathlib.Path(queue_path)
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        queue_data = json.load(f)

    missions = queue_data.get('missions', []) or []
    reset_ids = []

    for mission in missions:
        if mission.get('status') == 'ESCALATE' and mission.get('domain_id') == domain_id:
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(queue_data, f)

    return reset_ids


if __name__ == '__main__':
    args = sys.argv[1:]
    queue_path = 'MISSION_QUEUE.json'
    
    if '--domain' in args:
        idx = args.index('--domain')
        domain_id = args[idx + 1]
        print(reset_by_domain(queue_path, domain_id))
    else:
        print(reset_escalated(queue_path))

```python
import json
import pathlib
import sys


def reset_escalated(queue_path):
    """Reset status of all escalated missions to PENDING."""
    path = pathlib.Path(queue_path)
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        queue_data = json.load(f)

    missions = queue_data.get('missions', []) or []
    reset_ids = []

    for mission in missions:
        if mission.get('status') == 'ESCALATE':
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(queue_data, f)

    return reset_ids


def reset_by_domain(queue_path, domain_id):
    """Reset status of escalated missions for a specific domain."""
    path = pathlib.Path(queue_path)
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        queue_data = json.load(f)

    missions = queue_data.get('missions', []) or []
    reset_ids = []

    for mission in missions:
        if mission.get('status') == 'ESCALATE' and mission.get('domain_id') == domain_id:
            mission['status'] = 'PENDING'
            mission.pop('started_at', None)
            reset_ids.append(mission['id'])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(queue_data, f)

    return reset_ids


if __name__ == '__main__':
    args = sys.argv[1:]
    queue_path = 'MISSION_QUEUE.json'
    
    if '--domain' in args:
        idx = args.index('--domain')
        domain_id = args[idx + 1]
        print(reset_by_domain(queue_path, domain_id))
    else:
        print(reset_escalated(queue_path))
```