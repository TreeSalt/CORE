#!/bin/bash
# scripts/cold_start.sh — Full cold restart recovery
# USAGE: bash scripts/cold_start.sh
set -e
cd "$(dirname "$0")/.."
echo "============================================"
echo "AOS COLD START RECOVERY"
echo "============================================"
echo ""

# Step 1: Recover stale missions
echo "Step 1: Checking for stale IN_PROGRESS missions..."
.venv/bin/python3 -c "
import json
from pathlib import Path
from datetime import datetime, timezone

q = json.loads(Path('orchestration/MISSION_QUEUE.json').read_text())
stale = [m for m in q['missions'] if m.get('status') == 'IN_PROGRESS']
if stale:
    for m in stale:
        retries = m.get('retries', 0) + 1
        max_r = m.get('max_retries', 3)
        if retries > max_r:
            m['status'] = 'HARD_FAIL'
            m['cold_start_note'] = 'Exceeded max retries after cold restart'
            print(f'  HARD_FAIL: {m["id"]} (retries exhausted)')
        else:
            m['status'] = 'PENDING'
            m['retries'] = retries
            m['cold_start_note'] = f'Recovered from IN_PROGRESS at {datetime.now(timezone.utc).isoformat()}'
            print(f'  RECOVERED: {m["id"]} -> PENDING (retry {retries}/{max_r})')
    Path('orchestration/MISSION_QUEUE.json').write_text(json.dumps(q, indent=2))
    print(f'\nRecovered {len(stale)} stale missions')
else:
    print('  No stale missions found. Clean state.')
"
echo ""

# Step 2: Verify engine version
echo "Step 2: Engine version check..."
.venv/bin/python3 -c "import mantis_core; print(f'  Version: {mantis_core.__version__}')"
echo ""

# Step 3: Check Ollama
echo "Step 3: Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Ollama is running"
else
    echo "  Starting Ollama with GPU offload..."
    OLLAMA_NUM_GPU=20 ollama serve &
    sleep 5
    echo "  Ollama started"
fi
echo ""

# Step 4: Queue summary
echo "Step 4: Queue status..."
.venv/bin/python3 -c "
import json
from pathlib import Path
q = json.loads(Path('orchestration/MISSION_QUEUE.json').read_text())
statuses = {}
for m in q['missions']:
    s = m.get('status', 'UNKNOWN')
    statuses[s] = statuses.get(s, 0) + 1
for s, c in sorted(statuses.items()):
    print(f'  {s}: {c}')
"
echo ""

echo "============================================"
echo "COLD START COMPLETE — Ready to run"
echo "============================================"
echo ""
echo "Next: .venv/bin/python3 scripts/orchestrator_loop.py"
