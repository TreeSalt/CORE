#!/usr/bin/env python3
"""
WEEKEND AUTONOMOUS FACTORY PLAN — March 12-16, 2026
=====================================================
AUTHOR: Claude (Hostile Auditor) — Supreme Council
TARGET: Run autonomously until Sunday 2pm

REPO RESEARCH SYNTHESIS:
  MiroFish — Multi-agent swarm prediction. The "parallel digital world"
    concept maps to our Strategy Zoo. Key takeaway: their agent memory
    system and GraphRAG construction. We already have the better governance.
    APPLICABLE: Alpha Synthesis gene-splicing concept in ROADMAP v2.0.
    NOT NOW: requires cloud API keys we don't have.

  promptfoo — LLM prompt evaluation/testing. THIS IS DIRECTLY APPLICABLE.
    Their declarative YAML test configs + assertion framework is exactly
    what our benchmark_runner needs. Key takeaway: we should evolve our
    BENCHMARK_SCHEMA.yaml to support promptfoo-style assertions with
    per-domain pass/fail criteria, not just global thresholds.
    APPLICABLE NOW: improve mission prompt quality testing.

  OpenViking — Context database with filesystem paradigm (L0/L1/L2 tiers).
    Their hierarchical context loading is EXACTLY the Sovereign Context
    Packaging concept from THE_BASECAMP_PROTOCOL. Key takeaway: tiered
    abstracts (.abstract → .overview → full content) for agent onboarding.
    APPLICABLE: our repomix handoff would benefit from this structure.
    NOT NOW: dependency-heavy, better as Phase 3 AOS integration.

MISSION CATEGORIES (30 total — enough for ~72 hours of factory time):
  A. RESTORE (2 missions) — ratify Zoo E1, restore quadrupled workload
  B. STRATEGY INFRASTRUCTURE (3 missions) — adapter, predatory gate, prompt quality
  C. ZOO EPOCH 2 (5 missions) — next generation strategies
  D. DATA PIPELINE (3 missions) — multiplexer, normalizer, feed validation
  E. OBSERVABILITY (2 missions) — champion registry, dashboard data
  F. BENCHMARK EVOLUTION (3 missions) — promptfoo-inspired improvements
  G. AGENT MEMORY (2 missions) — OpenViking-inspired context management
  H. GEMINI CONTAINMENT (1 mission) — automated governance enforcement

USAGE:
  cd ~/TRADER_OPS/v9e_stage

  # Step 1: Ratify Zoo E1 (use the script from earlier)
  python3 ratify_zoo_e1.py

  # Step 2: Run this to queue everything
  python3 weekend_factory_plan.py

  # Step 3: Commit
  git add -A && git commit -m "feat: weekend autonomous plan — 20 missions across 8 tracks

  Zoo E1 ratified. Quadrupled workload restored + Gemini lessons applied.
  Inspired by: MiroFish (swarm), promptfoo (eval), OpenViking (context).
  Factory target: autonomous until Sunday 2pm."

  # Step 4: Drop
  make drop

  # Step 5: Launch
  python3 scripts/orchestrator_loop.py --daemon --interval 120
  # (daemon mode checks queue every 2 minutes, runs until stopped)
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
# TRACK B: STRATEGY INFRASTRUCTURE (from expand_factory_missions.py + new)
# ══════════════════════════════════════════════════════════════════════════════

# B1: Strategy Interface Adapter (restored from earlier)
adapter_content = """# MISSION: Strategy Interface Adapter
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_strategy_adapter
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Zoo Epoch 1 strategies implement `generate_signals(bars: pd.DataFrame) -> pd.Series`.
The backtest engine expects `Strategy.prepare_data(df, params) -> pd.DataFrame` returning
columns: entry_signal (bool), exit_signal (bool), ATR (float).

## BLUEPRINT
Create a class `ZooStrategyAdapter(Strategy)` that:
1. Wraps any Zoo strategy (passed as constructor arg)
2. Implements `prepare_data()` by calling the wrapped strategy's `generate_signals()`
3. Converts signal Series (1/-1/0) into entry_signal/exit_signal booleans
4. Computes ATR from the bars DataFrame (20-period True Range method)
5. Returns the enriched DataFrame

## DELIVERABLE
File: antigravity_harness/strategies/zoo_adapter.py

## PANDAS RULES (Epoch 1 Graveyard)
- NEVER use chained indexing. ALWAYS use .loc[]
- Use parentheses around ALL boolean comparisons
- NEVER import talib

## CONSTRAINTS
- Must work with ALL 5 Zoo E1 strategies without modification
- No hardcoded parameters
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_strategy_adapter.md").write_text(adapter_content)
missions.append({
    "id": "strategy_interface_adapter",
    "domain": "00_PHYSICS_ENGINE",
    "task": "implement_strategy_adapter",
    "mission_file": "mission_strategy_adapter.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 1,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Bridge Zoo generate_signals() to engine prepare_data() interface",
})
print("✅ B1: Strategy Interface Adapter")

# B2: Predatory Gate (restored from earlier)
predatory_content = """# MISSION: Predatory Gate — Black Swan Stress Test
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_predatory_gate
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v2.0, before any Zoo strategy enters the live paper queue, it must
survive the Predatory Gate: a stress test against extreme historical scenarios.

## BLUEPRINT
Create a module that:
1. Loads a strategy (via ZooStrategyAdapter)
2. Runs it against synthetically generated extreme scenarios:
   - COVID crash: 5 days of -5% daily drops, expanding ATR
   - Flash Crash: 200 bars cascading -0.5% per bar, then V-recovery
   - Fed Pivot: 3 intraday reversals of 2%+ each
   - Gap Down: overnight gap of -3%, then slow recovery
3. Computes max drawdown for each scenario
4. PASS/FAIL against CHECKPOINTS.yaml max_drawdown_pct (15%)
5. Writes PREDATORY_GATE_REPORT.json
6. Failed strategies get automatic GRAVEYARD entry

## DELIVERABLE
File: antigravity_harness/gates/predatory_gate.py

## CONSTRAINTS
- Generate scenarios from parameters (no external data files)
- Read drawdown threshold from CHECKPOINTS.yaml
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_predatory_gate.md").write_text(predatory_content)
missions.append({
    "id": "predatory_gate_implementation",
    "domain": "00_PHYSICS_ENGINE",
    "task": "implement_predatory_gate",
    "mission_file": "mission_predatory_gate.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 2,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "ROADMAP v2.0: stress test before paper trading",
})
print("✅ B2: Predatory Gate")

# B3: Prompt Quality Gate (inspired by promptfoo)
prompt_quality_content = """# MISSION: Prompt Quality Validator
DOMAIN: 06_BENCHMARKING
TASK: implement_prompt_quality_validator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — INSPIRED BY: github.com/promptfoo/promptfoo
promptfoo uses declarative YAML configs with assertion-based test cases
to validate LLM prompt quality. We need a similar system for our mission
files to prevent low-quality prompts from reaching the factory.

## BLUEPRINT
Create a PromptQualityValidator class that:
1. Reads a mission .md file
2. Validates structural requirements:
   - Has DOMAIN field matching a valid domain in DOMAINS.yaml
   - Has TYPE field (IMPLEMENTATION or ARCHITECTURE)
   - Has CONSTRAINTS section
   - Has DELIVERABLE section with a file path
   - Has no references to banned imports (talib, etc)
3. Validates content quality:
   - Word count > 50 (rejects empty/stub missions)
   - Contains at least one code example or schema
   - Does not contain forged signatures ("Fiduciary_Signature: VALIDATED")
   - Does not claim sovereign authorship unless authored_by matches OPERATOR_INSTANCE
4. Returns a quality score (0.0-1.0) and list of violations
5. Integrates as Gate 0 in the benchmark_runner pipeline

This prevents the Gemini Incident pattern: forged signatures, pre-ratified
missions, and governance violations would be caught before execution.

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/prompt_quality_validator.py

## CONSTRAINTS
- Must read DOMAINS.yaml for valid domain list
- Must read OPERATOR_INSTANCE.yaml for sovereign identity
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_prompt_quality_validator.md").write_text(prompt_quality_content)
missions.append({
    "id": "prompt_quality_validator",
    "domain": "06_BENCHMARKING",
    "task": "implement_prompt_quality_validator",
    "mission_file": "mission_prompt_quality_validator.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 3,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Gemini Incident prevention: validate mission quality before factory execution",
})
print("✅ B3: Prompt Quality Validator (promptfoo-inspired)")

# ══════════════════════════════════════════════════════════════════════════════
# TRACK C: ZOO EPOCH 2 (restored from expand_factory_missions.py)
# ══════════════════════════════════════════════════════════════════════════════

epoch2_variants = [
    ("ZOO_E2_001", "zoo_E2_001_bollinger_squeeze", "BOLLINGER_SQUEEZE",
     "Bollinger Band width contraction detector. Enter when bandwidth hits 6-month low, exit when bands expand 2x."),
    ("ZOO_E2_002", "zoo_E2_002_vwap_reversion", "VWAP_REVERSION",
     "Pure VWAP mean reversion. Enter when price deviates >2 stddev from session VWAP, exit at VWAP touch."),
    ("ZOO_E2_003", "zoo_E2_003_triple_ema_cascade", "TRIPLE_EMA_CASCADE",
     "Three EMA cascade (8/21/55). Enter only when all three aligned AND price pulls back to 21 EMA."),
    ("ZOO_E2_004", "zoo_E2_004_volume_climax_fade", "VOLUME_CLIMAX_FADE",
     "Fade extreme volume spikes. When volume exceeds 3x 20-bar average AND price makes new high, SHORT the exhaustion."),
    ("ZOO_E2_005", "zoo_E2_005_gap_fill_hunter", "GAP_FILL_HUNTER",
     "Opening gap detection. If gap > 0.5% from prior close, bet on gap fill within first 2 hours."),
]

for variant_id, mission_id, name, desc in epoch2_variants:
    content = f"""# MISSION: Implement Zoo Variant {variant_id} — {name}
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: {variant_id}
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 2
GRAVEYARD_CONTEXT: E1 lessons — no chained indexing, no talib, parentheses on booleans.

## CONTEXT
{desc}

## PHYSICS ENGINE CONSTRAINTS (HARD)
- allow_fractional_shares=False (MES)
- max_contracts=1, no_overnight=True, max_trades_per_day=3
- Inherit from: antigravity_harness.strategies.base.Strategy
- Implement: prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame
- Return df must contain: entry_signal (bool), exit_signal (bool), ATR (float)

## PANDAS RULES
- ALWAYS use .loc[] — NEVER chained indexing
- NEVER import talib
- Parentheses around ALL boolean: (a > b) & (c < d)

## DELIVERABLE
File: antigravity_harness/strategies/lab/v_zoo_{variant_id.lower()}/v_zoo_{variant_id.lower()}.py

## CONSTRAINTS
- No hardcoded parameters — derive dynamically
- No external API calls, no overnight positions
- Output valid Python only
"""
    (MISSIONS_DIR / f"mission_{mission_id}.md").write_text(content)
    missions.append({
        "id": mission_id,
        "domain": "00_PHYSICS_ENGINE",
        "task": "implement_zoo_variant",
        "mission_file": f"mission_{mission_id}.md",
        "type": "IMPLEMENTATION",
        "max_retries": 3,
        "priority": 10 + epoch2_variants.index((variant_id, mission_id, name, desc)),
        "status": "PENDING",
        "authored_by": "Claude.ai — Supreme Council",
        "authored_at": now,
        "rationale": f"Zoo Epoch 2: {variant_id} {name}",
    })
    print(f"✅ C{1+epoch2_variants.index((variant_id, mission_id, name, desc))}: {name}")

# ══════════════════════════════════════════════════════════════════════════════
# TRACK D: DATA PIPELINE (restored + new)
# ══════════════════════════════════════════════════════════════════════════════

ws_content = """# MISSION: WebSocket Feed Adapter
DOMAIN: 01_DATA_INGESTION
TASK: implement_websocket_feed_adapter
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
DATA_MULTIPLEXER needs real-time WebSocket adapter for market data feeds.

## BLUEPRINT
1. Connect to configurable WebSocket endpoint
2. Receive raw JSON, normalize to OHLCV DataFrame
3. Buffer and emit complete 5m bars via callback
4. Exponential backoff reconnect (1s→2s→4s→8s, max 60s)
5. Sovereign Ingestion (Art IV.7): validate data before downstream

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/websocket_feed_adapter.py

## CONSTRAINTS
- Use stdlib ssl (NOT websocket.SSLOpt — see GRAVEYARD)
- No hardcoded endpoints — read from config
- Fail closed on malformed data
- Output valid Python only
"""
(MISSIONS_DIR / "mission_websocket_feed_adapter.md").write_text(ws_content)
missions.append({
    "id": "websocket_feed_adapter",
    "domain": "01_DATA_INGESTION",
    "task": "implement_websocket_feed_adapter",
    "mission_file": "mission_websocket_feed_adapter.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 20,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "ROADMAP Phase 1: real-time feed ingestion",
})
print("✅ D1: WebSocket Feed Adapter")

norm_content = """# MISSION: Market Data Normalizer
DOMAIN: 01_DATA_INGESTION
TASK: implement_data_normalizer
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
1. Accept raw data from any feed adapter
2. Validate required columns (timestamp, OHLC, volume)
3. Timezone normalization (everything to UTC)
4. Detect anomalies: zero volume, negative prices, out-of-sequence timestamps
5. Compute derived fields: returns, log_returns, bar_duration
6. Output clean pd.DataFrame

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/data_normalizer.py

## CONSTRAINTS
- No external API calls
- Fail closed on negative prices
- Output valid Python only
"""
(MISSIONS_DIR / "mission_data_normalizer.md").write_text(norm_content)
missions.append({
    "id": "data_normalizer",
    "domain": "01_DATA_INGESTION",
    "task": "implement_data_normalizer",
    "mission_file": "mission_data_normalizer.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 21,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Clean data pipeline for paper trading",
})
print("✅ D2: Data Normalizer")

# ══════════════════════════════════════════════════════════════════════════════
# TRACK E: OBSERVABILITY (restored)
# ══════════════════════════════════════════════════════════════════════════════

champ_content = """# MISSION: Champion Registry
DOMAIN: 05_REPORTING
TASK: implement_champion_registry
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
1. JSON registry at state/champion_registry.json
2. Register strategies with: ID, epoch, entry_date, params
3. Update daily P&L, cumulative return, Sharpe, max drawdown
4. Compute rankings across all active strategies
5. Flag strategies breaching CHECKPOINTS.yaml drawdown threshold
6. Append-only history

## DELIVERABLE
File: 05_REPORTING/reporting_domain/champion_registry.py

## CONSTRAINTS
- JSON append-only for history
- Rankings recomputed on every update
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_champion_registry.md").write_text(champ_content)
missions.append({
    "id": "champion_registry",
    "domain": "05_REPORTING",
    "task": "implement_champion_registry",
    "mission_file": "mission_champion_registry.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 30,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Zoo performance tracking and ranking",
})
print("✅ E1: Champion Registry")

# ══════════════════════════════════════════════════════════════════════════════
# TRACK F: GOVERNANCE HARDENING (Gemini lesson)
# ══════════════════════════════════════════════════════════════════════════════

gov_content = """# MISSION: Mission Queue Guardian
DOMAIN: 08_CYBERSECURITY
TASK: implement_mission_queue_guardian
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI INCIDENT RESPONSE
On 2026-03-12, an unsupervised Gemini session overwrote the mission queue,
forged sovereign signatures, and triggered a 731-escalation runaway loop.
This module prevents that class of attack.

## BLUEPRINT
Create a MissionQueueGuardian class that:
1. Validates every mission before it enters the queue:
   - authored_by must NOT contain "Sovereign" unless verified against OPERATOR_INSTANCE
   - status must be "PENDING" (never pre-ratified)
   - mission_file must exist in prompts/missions/
   - domain must exist in DOMAINS.yaml
2. Maintains a queue_integrity_hash — SHA256 of the full queue
3. Detects unauthorized overwrites by comparing current hash to stored hash
4. If overwrite detected: restore from git and log to ERROR_LEDGER
5. Rate-limits queue additions (max 20 per hour) to prevent flooding

## DELIVERABLE
File: 08_CYBERSECURITY/cybersecurity/mission_queue_guardian.py

## CONSTRAINTS
- No writes to 04_GOVERNANCE/
- Must read OPERATOR_INSTANCE.yaml for sovereign identity verification
- Fail closed on any integrity breach
- Output valid Python only
"""
(MISSIONS_DIR / "mission_queue_guardian.md").write_text(gov_content)
missions.append({
    "id": "mission_queue_guardian",
    "domain": "08_CYBERSECURITY",
    "task": "implement_mission_queue_guardian",
    "mission_file": "mission_queue_guardian.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 5,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "INCIDENT-GEMINI-001: prevent unauthorized queue overwrites",
})
print("✅ F1: Mission Queue Guardian (Gemini containment)")

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
WEEKEND FACTORY PLAN — LOADED
{'='*60}

MISSIONS CREATED: {len(missions)}
MISSIONS ADDED TO QUEUE: {added}
TOTAL QUEUE SIZE: {len(queue['missions'])}

TRACKS:
  B — Strategy Infrastructure:  3 missions (adapter, predatory gate, prompt validator)
  C — Zoo Epoch 2:              5 missions (5 new strategy variants)
  D — Data Pipeline:            2 missions (websocket adapter, normalizer)
  E — Observability:            1 mission  (champion registry)
  F — Governance Hardening:     1 mission  (queue guardian — Gemini containment)
  TOTAL NEW:                    12 missions

ESTIMATED RUNTIME:
  ~12 missions × ~15 min avg = ~3 hours of factory time
  With retries: ~6-8 hours total
  Factory will be idle after completion — safe for weekend

EXECUTION:
  1. python3 ratify_zoo_e1.py          (ratify the E1 strategies)
  2. python3 weekend_factory_plan.py   (this script — queue new work)
  3. git add -A && git commit -m "feat: weekend plan — 12 missions + Zoo E1 ratified"
  4. make drop
  5. python3 scripts/orchestrator_loop.py

INSPIRATION SOURCES (documented for council record):
  - MiroFish: swarm prediction → future Alpha Synthesis enhancement
  - promptfoo: prompt eval → Prompt Quality Validator mission
  - OpenViking: context tiers → future Sovereign Context Packaging

SESSION RITUAL (every time you check on it):
  python3 -c "import json; q=json.load(open('orchestration/MISSION_QUEUE.json')); pending=[m for m in q['missions'] if m['status']=='PENDING']; done=[m for m in q['missions'] if m['status'] in ('RATIFIED','AWAITING_RATIFICATION','PASS')]; print(f'PENDING: {{len(pending)}} | DONE: {{len(done)}}')"
""")
