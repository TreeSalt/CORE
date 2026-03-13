#!/usr/bin/env python3
"""
42-HOUR WEEKEND SPRINT — Friday 19:46 → Sunday 14:00
=====================================================
AUTHOR: Claude (Hostile Auditor) — Supreme Council
DATE: 2026-03-13

COMPUTE BUDGET: ~42 hours of factory time
  32b model: ~15 min/mission = ~168 mission slots
  7b model: ~2 min/mission = ~1260 mission slots
  Realistic with mixed routing: ~40-60 missions

STRATEGY: Fill the queue with layered work so the factory
always has something productive to do. Missions are prioritized
so the highest-value work runs first, and lower-priority work
fills idle time.

PRIORITY TIERS:
  P0 (CRITICAL): Must complete before Sunday review
  P1 (HIGH):     Directly advances CP1 timeline  
  P2 (MEDIUM):   Infrastructure and tooling
  P3 (LOW):      Research and future-phase prep

INCORPORATES GEMINI'S SUGGESTIONS:
  - Compute scheduler for VRAM contention
  - Capital allocation mechanism for multi-strategy paper trading
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
# P0 — CRITICAL: Predatory Gate on new strategies
# ══════════════════════════════════════════════════════════════════════════════

# The E2.5 resurrections and E3 pairs need to face the gauntlet
gate_batch_content = """# MISSION: Predatory Gate Batch Runner v2
DOMAIN: 06_BENCHMARKING
TASK: implement_predatory_gate_batch_v2
TYPE: IMPLEMENTATION
VERSION: 2.0

## CONTEXT
The Predatory Gate v2 runner exists at scripts/run_predatory_gate.py.
However, new strategies (E2.5 resurrections + E3 pairs) were just ratified
and need to be tested. The current runner discovers strategies from
proposals but doesn't distinguish which have already been tested.

## BLUEPRINT
Create an incremental gate runner that:
1. Reads state/PREDATORY_GATE_REPORT.json for already-tested strategies
2. Scans 08_IMPLEMENTATION_NOTES/ for RATIFIED proposals NOT in the report
3. Runs ONLY the new untested strategies through all 4 scenarios
4. Merges results into the existing PREDATORY_GATE_REPORT.json
5. Updates state/predatory_gate_survivors.json with new survivors
6. Updates state/champion_registry.json with new entries

This enables incremental testing: run the gate after every factory batch
without re-testing strategies that already passed or failed.

## DELIVERABLE
File: scripts/run_predatory_gate_incremental.py

## CONSTRAINTS
- Must preserve existing report data (append, not overwrite)
- Must use .venv/bin/python3 (numpy/pandas in venv)
- Use same scenario generators as run_predatory_gate.py
- Same BaseStrategy shim for E1-era code
- Output valid Python only
"""
(MISSIONS_DIR / "mission_predatory_gate_incremental.md").write_text(gate_batch_content)
missions.append({
    "id": "predatory_gate_incremental",
    "domain": "06_BENCHMARKING",
    "task": "implement_predatory_gate_batch_v2",
    "mission_file": "mission_predatory_gate_incremental.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 0,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P0: Predatory Gate Incremental Runner")

# ══════════════════════════════════════════════════════════════════════════════
# P1 — HIGH: Capital Allocation + Compute Scheduling (Gemini suggestions)
# ══════════════════════════════════════════════════════════════════════════════

capital_content = """# MISSION: Capital Allocator — Multi-Strategy Splitter
DOMAIN: 02_RISK_MANAGEMENT
TASK: implement_capital_allocator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI STRATEGIC SUGGESTION
When multiple strategies survive the Predatory Gate and enter paper trading
simultaneously, the system needs to decide how to split the $2,000 baseline
across competing strategies without violating MES integer-lot physics
($5/tick, 1 contract minimum).

## BLUEPRINT
Create a CapitalAllocator class that:
1. Reads state/predatory_gate_survivors.json for active strategies
2. Reads state/champion_registry.json for performance metrics
3. Allocates capital based on risk-adjusted ranking:
   - Equal weight: split evenly (baseline approach)
   - Sharpe-weighted: allocate proportional to rolling Sharpe
   - Inverse-volatility: more capital to lower-vol strategies
4. Enforces integer-lot constraint: MES = 1 contract minimum
   - With $2,000 and 1-contract minimum, max 2 concurrent strategies
   - If 3+ survivors, allocator ranks and selects top N
5. Rebalances daily based on updated Champion Registry metrics
6. Writes allocation decisions to state/capital_allocation.json
7. Risk manager must approve all allocations before execution

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/capital_allocator.py

## CONSTRAINTS
- Total allocation must never exceed CHECKPOINTS.yaml capital limit
- Integer lots only (no fractional MES contracts)
- Fail closed if Risk Manager rejects allocation
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_capital_allocator.md").write_text(capital_content)
missions.append({
    "id": "capital_allocator",
    "domain": "02_RISK_MANAGEMENT",
    "task": "implement_capital_allocator",
    "mission_file": "mission_capital_allocator.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 5,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P1: Capital Allocator")

compute_content = """# MISSION: Compute Scheduler — VRAM Resource Manager
DOMAIN: 03_ORCHESTRATION
TASK: implement_compute_scheduler
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI STRATEGIC SUGGESTION
As the Champion Registry grows, the orchestrator needs a strict local
resource scheduler to prevent the 32b Heavy Lifter from colliding with
the paper trading data streams. The GTX 1070 has 8GB VRAM and 32GB
system RAM — both are shared resources.

## BLUEPRINT
Create a ComputeScheduler class that:
1. Reads orchestration/VRAM_STATE.json for current GPU utilization
2. Maintains a priority queue of compute requests:
   - P0: Paper trading (real-time, cannot be interrupted)
   - P1: Predatory Gate runs (time-sensitive)
   - P2: Factory missions (can wait)
   - P3: Background tasks (lowest priority)
3. Before dispatching a mission to Ollama:
   - Check VRAM availability (8GB total, model needs vary)
   - If 32b model needed but paper trading is running → queue
   - If 7b model suffices → dispatch immediately (fits alongside)
4. Writes scheduling decisions to state/compute_schedule.json
5. Provides should_dispatch(model_size, priority) -> bool

## DELIVERABLE
File: 03_ORCHESTRATION/orchestration_domain/compute_scheduler.py

## CONSTRAINTS
- Never interrupt P0 (paper trading) for P2 (factory) work
- Must be queryable by orchestrator_loop.py before dispatch
- Log all scheduling decisions
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_compute_scheduler.md").write_text(compute_content)
missions.append({
    "id": "compute_scheduler",
    "domain": "03_ORCHESTRATION",
    "task": "implement_compute_scheduler",
    "mission_file": "mission_compute_scheduler.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 6,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P1: Compute Scheduler")

# ══════════════════════════════════════════════════════════════════════════════
# P1 — HIGH: More Zoo Strategies (keep the pipeline fed)
# ══════════════════════════════════════════════════════════════════════════════

epoch3_variants = [
    ("E3_002", "zoo_E3_002_rsi_divergence", "RSI_DIVERGENCE",
     "Detect RSI divergence from price. When price makes new high but RSI doesn't confirm, fade the move. Classic momentum exhaustion signal."),
    ("E3_003", "zoo_E3_003_market_profile_value", "MARKET_PROFILE_VALUE",
     "Identify the Point of Control (highest volume price) from the prior session. Trade mean reversion toward POC when price deviates >1 ATR."),
    ("E3_004", "zoo_E3_004_overnight_range_trap", "OVERNIGHT_RANGE_TRAP",
     "Detect when the opening 15min price is within the overnight high-low range. If range is tight (<0.5%), bet on breakout in the direction of the first 15min close."),
]

for vid, mid, name, desc in epoch3_variants:
    content = f"""# MISSION: {vid} — {name}
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
TYPE: IMPLEMENTATION
EPOCH: 3
GRAVEYARD_CONTEXT: E1 died from chained indexing, talib, missing .loc[]. E2.5 resurrections applied these fixes. Continue this discipline.

## BLUEPRINT
{desc}

## PHYSICS ENGINE CONSTRAINTS (HARD)
- Inherit from Strategy, implement prepare_data()
- Return: entry_signal (bool), exit_signal (bool), ATR (float)
- .loc[] only, no talib, parentheses on booleans
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- No external API calls
- Output valid Python only

## DELIVERABLE
File: antigravity_harness/strategies/lab/v_zoo_{vid.lower()}/v_zoo_{vid.lower()}_{name.lower()}.py
"""
    (MISSIONS_DIR / f"mission_{mid}.md").write_text(content)
    missions.append({
        "id": mid,
        "domain": "00_PHYSICS_ENGINE",
        "task": "implement_zoo_variant",
        "mission_file": f"mission_{mid}.md",
        "type": "IMPLEMENTATION",
        "max_retries": 3,
        "priority": 12 + epoch3_variants.index((vid, mid, name, desc)),
        "status": "PENDING",
        "authored_by": "Claude.ai — Supreme Council",
        "authored_at": now,
    })
    print(f"✅ P1: {vid} {name}")

# ══════════════════════════════════════════════════════════════════════════════
# P2 — MEDIUM: Trade Ledger + Performance Reporter
# ══════════════════════════════════════════════════════════════════════════════

ledger_content = """# MISSION: Immutable Trade Ledger
DOMAIN: 05_REPORTING
TASK: implement_trade_ledger
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the paper trading system needs an append-only trade ledger
that records every fill, every P&L event, and every risk decision.
This is the evidentiary foundation for CP1 qualification.

## BLUEPRINT
Create a TradeLedger class that:
1. Stores trades in state/trade_ledger.jsonl (one JSON line per event)
2. Events: ENTRY, EXIT, STOP_HIT, DMS_TRIP, RISK_REJECT, DAY_END_FLATTEN
3. Each event has: timestamp, strategy_id, direction, price, quantity,
   pnl (for exits), cumulative_pnl, equity, drawdown_pct
4. The file is APPEND-ONLY — no deletions, no modifications
5. Each line includes a running SHA256 hash chain (hash of previous line)
6. Provides query methods: by_strategy, by_date_range, summary_stats
7. CP1 qualification check: count trades, compute Sharpe, compute max DD

## DELIVERABLE
File: 05_REPORTING/reporting_domain/trade_ledger.py

## CONSTRAINTS
- Append-only (constitutional requirement for CP1 evidence)
- Hash chain for tamper detection
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_trade_ledger.md").write_text(ledger_content)
missions.append({
    "id": "immutable_trade_ledger",
    "domain": "05_REPORTING",
    "task": "implement_trade_ledger",
    "mission_file": "mission_trade_ledger.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 15,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P2: Immutable Trade Ledger")

perf_content = """# MISSION: Performance Reporter — CP1 Qualification Dashboard
DOMAIN: 05_REPORTING
TASK: implement_performance_reporter
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
Create a PerformanceReporter class that:
1. Reads state/trade_ledger.jsonl for trade history
2. Computes per-strategy and portfolio-level metrics:
   - Sharpe ratio (annualized), Sortino ratio
   - Max drawdown (%), Calmar ratio
   - Win rate, profit factor, avg win/loss ratio
   - Total trades, avg hold time, trades per day
3. Computes CP1 qualification status:
   - Days elapsed (need 90), Trades count (need 250)
   - Rolling 90d Sharpe (need >= 2.5), Max DD (need <= 15%)
4. Outputs a human-readable report to state/performance_report.md
5. Outputs machine-readable JSON to state/performance_report.json

## DELIVERABLE
File: 05_REPORTING/reporting_domain/performance_reporter.py

## CONSTRAINTS
- Read-only access to trade ledger
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_performance_reporter.md").write_text(perf_content)
missions.append({
    "id": "performance_reporter",
    "domain": "05_REPORTING",
    "task": "implement_performance_reporter",
    "mission_file": "mission_performance_reporter.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 16,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P2: Performance Reporter")

# ══════════════════════════════════════════════════════════════════════════════
# P3 — LOW: AOS Boundary Audit + Red Team Test Suite
# ══════════════════════════════════════════════════════════════════════════════

boundary_content = """# MISSION: AOS Boundary Audit — Engine vs Payload Classification
DOMAIN: 07_INTEGRATION
TASK: implement_boundary_audit
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, Phase 3 requires splitting the monorepo into AOS (open-source
engine) and TRADER_OPS (commercial payload). Before that split can happen,
every file must be classified as ENGINE or PAYLOAD.

## BLUEPRINT
Create AOS_BOUNDARY_AUDIT.md that:
1. Lists every directory in the repo
2. Classifies each as ENGINE (goes to AOS) or PAYLOAD (stays in TRADER_OPS)
3. Identifies SHARED files that both repos need (e.g., base classes)
4. Documents extraction strategy: git subtree split commands
5. Lists files that need refactoring before split (tight coupling)

Classification rules:
- 04_GOVERNANCE/ → ENGINE (universal governance)
- 03_ORCHESTRATION/ → ENGINE (universal orchestration)
- 06_BENCHMARKING/ → ENGINE (universal benchmarking)
- 08_CYBERSECURITY/ → ENGINE (universal security)
- 00_PHYSICS_ENGINE/ → PAYLOAD (trading-specific)
- 01_DATA_INGESTION/ → PAYLOAD (market data specific)
- antigravity_harness/strategies/ → PAYLOAD
- antigravity_harness/execution/ → PAYLOAD
- antigravity_harness/instruments/ → PAYLOAD
- scripts/ → MIXED (some engine, some payload)

## DELIVERABLE
File: docs/AOS_BOUNDARY_AUDIT.md

## CONSTRAINTS
- ARCHITECTURE proposal — document, not code
- Must cover every top-level directory
- Must identify tight coupling points
- Output valid markdown only
"""
(MISSIONS_DIR / "mission_boundary_audit.md").write_text(boundary_content)
missions.append({
    "id": "aos_boundary_audit",
    "domain": "07_INTEGRATION",
    "task": "implement_boundary_audit",
    "mission_file": "mission_boundary_audit.md",
    "type": "ARCHITECTURE",
    "max_retries": 2,
    "priority": 25,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P3: AOS Boundary Audit (ARCHITECTURE — auto-ratifies)")

redteam_suite_content = """# MISSION: Red Team Test Suite — Validate Governance Gates
DOMAIN: 08_CYBERSECURITY
TASK: implement_redteam_test_suite
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The adversarial prompt generator exists (ratified). Now we need a test
suite that actually RUNS the generated adversarial prompts against the
benchmark runner and validates they get caught.

## BLUEPRINT
Create a test script that:
1. Generates adversarial mission files (using the generator)
2. For each adversarial probe:
   a. Runs it through benchmark_runner.py
   b. Asserts the benchmark REJECTS it
   c. Validates the rejection reason matches expected pattern
3. Test categories:
   - HALLUCINATION: imports talib, gitpython → expect HALLUCINATED_IMPORT
   - GOVERNANCE: writes to 04_GOVERNANCE/ → expect GOVERNANCE_VIOLATION
   - FORGERY: Authored_By: Sovereign → expect FORGERY_DETECTED
   - PRE_RATIFY: Status: RATIFIED → expect PRE_RATIFICATION
4. Produces a RED_TEAM_REPORT.json with pass/fail per probe
5. Overall: if ANY adversarial prompt PASSES the benchmark → CRITICAL ALERT

## DELIVERABLE
File: 08_CYBERSECURITY/cybersecurity/red_team_test_suite.py

## CONSTRAINTS
- Must not actually deploy adversarial missions
- Must clean up generated test files after running
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_redteam_test_suite.md").write_text(redteam_suite_content)
missions.append({
    "id": "red_team_test_suite",
    "domain": "08_CYBERSECURITY",
    "task": "implement_redteam_test_suite",
    "mission_file": "mission_redteam_test_suite.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 26,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
})
print("✅ P3: Red Team Test Suite")

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
42-HOUR WEEKEND SPRINT — LOADED
{'='*60}

P0 CRITICAL (must complete):
  1. Predatory Gate Incremental Runner

P1 HIGH (advances CP1):
  2. Capital Allocator (Gemini suggestion)
  3. Compute Scheduler (Gemini suggestion)
  4. E3_002 RSI Divergence
  5. E3_003 Market Profile Value
  6. E3_004 Overnight Range Trap

P2 MEDIUM (infrastructure):
  7. Immutable Trade Ledger (CP1 evidence)
  8. Performance Reporter (CP1 dashboard)

P3 LOW (future-phase prep):
  9. AOS Boundary Audit (ARCHITECTURE — auto-ratifies)
  10. Red Team Test Suite

TOTAL: {len(missions)} missions ({added} added to queue)
ESTIMATED TIME: 3-5 hours (leaves 37+ hours buffer for retries)

AFTER FACTORY COMPLETES:
  Sunday review agenda:
  1. Ratify the batch
  2. Deploy incremental gate runner
  3. Run E2.5 + E3 strategies through Predatory Gate
  4. New survivors join paper trading matrix
  5. Trade ledger + performance reporter enable CP1 tracking
  6. AOS boundary audit documents the Phase 3 split

EXECUTION:
  git add -A && git commit -m "feat: 42h weekend sprint — 10 missions across 4 priority tiers"
  make drop
  python3 scripts/orchestrator_loop.py
""")
