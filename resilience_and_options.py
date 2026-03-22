#!/usr/bin/env python3
"""
RESILIENCE + OPTIONS ARCHITECTURE
==================================
1. Fix stale IN_PROGRESS detection for cold restart survival
2. Queue options instrument architecture for Phase 2
"""
import json
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(".")
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"
QUEUE_FILE = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
now = datetime.now(timezone.utc).isoformat()
missions = []

# ══════════════════════════════════════════════════════════════════════════════
# FIX 1: Cold restart resilience — stale mission recovery
# ══════════════════════════════════════════════════════════════════════════════

stale_content = """# MISSION: Cold Restart Resilience — Stale Mission Recovery
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
        print(f'  RECOVERING: {m[\"id\"]} → PENDING')
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
"""
(MISSIONS_DIR / "mission_cold_start_resilience.md").write_text(stale_content)
missions.append({
    "id": "cold_start_resilience",
    "domain": "03_ORCHESTRATION",
    "task": "implement_stale_mission_recovery",
    "mission_file": "mission_cold_start_resilience.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 2,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "System must survive power loss and cold restart without manual intervention",
})
print("✅ Cold Start Resilience")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 2: In the meantime, create cold_start.sh directly
# ══════════════════════════════════════════════════════════════════════════════

cold_start_script = REPO_ROOT / "scripts" / "cold_start.sh"
cold_start_script.write_text("""#!/bin/bash
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
            print(f'  HARD_FAIL: {m[\"id\"]} (retries exhausted)')
        else:
            m['status'] = 'PENDING'
            m['retries'] = retries
            m['cold_start_note'] = f'Recovered from IN_PROGRESS at {datetime.now(timezone.utc).isoformat()}'
            print(f'  RECOVERED: {m[\"id\"]} -> PENDING (retry {retries}/{max_r})')
    Path('orchestration/MISSION_QUEUE.json').write_text(json.dumps(q, indent=2))
    print(f'\\nRecovered {len(stale)} stale missions')
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
""")
cold_start_script.chmod(0o755)
print("✅ Created: scripts/cold_start.sh (deployable NOW)")

# ══════════════════════════════════════════════════════════════════════════════
# OPTIONS ARCHITECTURE — Phase 2 planning
# ══════════════════════════════════════════════════════════════════════════════

options_content = """# MISSION: Options Instrument Architecture
DOMAIN: 00_PHYSICS_ENGINE
TASK: design_options_instrument
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT — ROADMAP v3.0 Phase 2+ DELIVERABLE
The current Physics Engine supports futures only (MES). To capture
asymmetric opportunities (moonshots), we need an options instrument
class. Options provide:
- Defined risk: max loss = premium paid
- Asymmetric payoff: unlimited upside on calls, large upside on puts
- Leverage: control large notional with small capital
- Volatility trading: profit from IV expansion regardless of direction

## WHY NOT NOW
Per CHECKPOINTS.yaml, CP1 requires proving the system works on the
simplest possible instrument (MES futures). Options add:
- Greeks (delta/gamma/theta/vega) that change every tick
- Time decay that erodes position value daily
- Implied volatility surfaces that shift with market regime
- Exercise/assignment risk at expiration
- Spread strategies (verticals, straddles, condors)

The constitutional guardrails (max DD, DMS) must be battle-tested
on simple instruments before adding this complexity.

## BLUEPRINT (ARCHITECTURE ONLY)
Design the OptionsInstrumentSpec class:

1. OptionsInstrumentSpec extends InstrumentSpec:
   - underlying: InstrumentSpec (e.g., SPY, MES)
   - strike_price: float
   - expiration: datetime
   - option_type: CALL | PUT
   - contract_multiplier: int (typically 100 for equity options)

2. OptionsGreeks dataclass:
   - delta, gamma, theta, vega, rho
   - iv: implied volatility
   - time_to_expiry: float (years)

3. OptionsPricingEngine:
   - black_scholes(S, K, T, r, sigma) -> price
   - compute_greeks(S, K, T, r, sigma) -> OptionsGreeks
   - iv_from_price(market_price, S, K, T, r) -> float

4. OptionsStrategy interface extends Strategy:
   - prepare_data() returns: entry_signal, exit_signal, ATR,
     PLUS: preferred_strike, preferred_expiry, preferred_type
   - Risk manager validates: max_premium_per_trade, max_total_premium,
     max_theta_decay_per_day

5. Multi-leg support (future):
   - Vertical spreads, straddles, iron condors
   - Each leg is an independent OptionsInstrumentSpec
   - Combined P&L computed at portfolio level

Document as class skeletons with type hints and docstrings.

## DELIVERABLE
File: antigravity_harness/instruments/options_architecture.py

## CONSTRAINTS
- ARCHITECTURE only — class skeletons, not implementation
- Must reference existing InstrumentSpec interface
- Must define how the Risk Manager enforces options-specific limits
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_options_architecture.md").write_text(options_content)
missions.append({
    "id": "options_instrument_architecture",
    "domain": "00_PHYSICS_ENGINE",
    "task": "design_options_instrument",
    "mission_file": "mission_options_architecture.md",
    "type": "ARCHITECTURE",
    "max_retries": 2,
    "priority": 30,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Phase 2: Options enable asymmetric moonshot opportunities with defined risk",
})
print("✅ Options Instrument Architecture (ARCHITECTURE — auto-ratifies)")

# ══════════════════════════════════════════════════════════════════════════════
# UPDATE QUEUE
# ══════════════════════════════════════════════════════════════════════════════

queue = json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else {"missions": []}
existing_ids = {m["id"] for m in queue["missions"]}
added = 0
for m in missions:
    if m["id"] not in existing_ids:
        queue["missions"].append(m)
        added += 1
QUEUE_FILE.write_text(json.dumps(queue, indent=2))

print(f"""
{'='*60}
RESILIENCE + OPTIONS — LOADED
{'='*60}

IMMEDIATE (deployable now):
  scripts/cold_start.sh — run after any reboot:
    bash scripts/cold_start.sh

FACTORY MISSIONS:
  1. Cold Start Resilience — stale mission detection + recovery
  2. Options Instrument Architecture — class skeletons for Phase 2

COLD START PROCEDURE (after power loss):
  1. Power on, login
  2. bash scripts/cold_start.sh
     (recovers stale missions, checks Ollama, shows queue status)
  3. .venv/bin/python3 scripts/orchestrator_loop.py
     (resumes from where it left off)

OPTIONS ROADMAP:
  CP1 (now):    Futures only. Prove the system works simply.
  CP2 ($100):   Options ARCHITECTURE ratified. Greeks engine built.
  CP3 ($1000):  First options paper trades. Defined-risk strategies only.
                (buying calls/puts, vertical spreads — never naked selling)
  CP4 ($5000):  Multi-leg strategies. Portfolio-level Greek management.

  The moonshots come from BUYING options with defined risk:
    - Buy calls before expected breakout → max loss = premium
    - Buy puts as portfolio insurance → max loss = premium
    - Straddles before vol events → profit from big moves either way

  NEVER naked selling. Constitutional constraint. The DMS trips before
  you can lose more than the premium you paid.
""")
