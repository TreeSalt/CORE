# MISSION: Cold Restart Resilience — Stale Mission Recovery
DOMAIN: 03_ORCHESTRATION
TASK: implement_stale_mission_recovery
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
If the machine loses power mid-mission (while a model is generating),
that mission gets stuck at IN_PROGRESS forever. On cold restart, the
orchestrator skips it because it's not PENDING. The sovereign must
manually intervene. This violates the autonomy principle.

## BLUEPRINT
Add a pre-flight check to orchestrator_loop.py that:
1. On startup, scans MISSION_QUEUE.json for IN_PROGRESS missions
2. For each IN_PROGRESS mission, checks:
   a. Does a proposal file exist in 08_IMPLEMENTATION_NOTES/?
   b. If YES and it passed benchmark → mark AWAITING_RATIFICATION
   c. If NO or benchmark failed → reset to PENDING, increment retry count
   d. If retry count exceeds max_retries → mark HARD_FAIL
3. Logs all recovery actions to docs/ERROR_LEDGER.md
4. Also checks for missions stuck longer than 2 hours (timeout watchdog)
5. Writes a COLD_START_RECOVERY.json to state/ documenting what was recovered

Also create a simple startup script that handles the full cold-start:

```
#!/bin/bash
# scripts/cold_start.sh — Full cold restart recovery
cd ~/TRADER_OPS/v9e_stage
echo "=== COLD START RECOVERY ==="
echo "Checking for stale missions..."
.venv/bin/python3 -c "
import json
from pathlib import Path
q = json.loads(Path('orchestration/MISSION_QUEUE.json').read_text())
stale = [m for m in q['missions'] if m.get('status') == 'IN_PROGRESS']
if stale:
    for m in stale:
        print(f'  RECOVERING: {m["id"]} → PENDING')
        m['status'] = 'PENDING'
    Path('orchestration/MISSION_QUEUE.json').write_text(json.dumps(q, indent=2))
    print(f'Recovered {len(stale)} stale missions')
else:
    print('No stale missions found')
"
echo "Starting Ollama..."
OLLAMA_NUM_GPU=20 ollama serve &
sleep 5
echo "Starting orchestrator..."
.venv/bin/python3 scripts/orchestrator_loop.py
```

## DELIVERABLE
File: scripts/cold_start.sh + patch to scripts/orchestrator_loop.py

## CONSTRAINTS
- Must be idempotent (running twice is safe)
- Must log all recovery actions
- Never auto-ratify recovered missions
- Output valid code only
