#!/usr/bin/env python3
"""
MULTI-THREADED SPRINT — Paper Trading + Factory + Infrastructure
================================================================
AUTHOR: Claude (Hostile Auditor) — Supreme Council
DATE: 2026-03-13

ARCHITECTURE:
  THREAD 1: Paper Trading Matrix (runs continuously in background)
    - E2_001 Bollinger Squeeze + E2_002 VWAP Reversion
    - 4 time windows: 15d / 30d / 60d / 90d
    - Each window is an independent instance collecting data
    - Results feed Champion Registry for cross-window analysis

  THREAD 2: Strategy Factory (orchestrator keeps building)
    - Epoch 3: Alpha Synthesis hybrids from survivors + graveyard
    - Epoch 2.5: Fix E1 strategies using E2 lessons
    - New topology: pairs/correlation strategies

  THREAD 3: Infrastructure (non-trading roadmap items)
    - Auto-deploy pipeline (proposal → target path)
    - Intent Compiler implementation
    - Dashboard data API

All three threads run independently. Paper trading doesn't block
factory production. Factory production doesn't block infrastructure.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(".")
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"
QUEUE_FILE = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
STATE_DIR = REPO_ROOT / "state"

STATE_DIR.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).isoformat()
missions = []

# ══════════════════════════════════════════════════════════════════════════════
# THREAD 1: PAPER TRADING MATRIX CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# This isn't a factory mission — it's a config file the backtest engine reads
paper_trading_config = {
    "version": "1.0",
    "created_at": now,
    "description": "Multi-window paper trading matrix. Each instance runs independently.",
    "strategies": {
        "E2_001_BOLLINGER_SQUEEZE": {
            "proposal": "PROPOSAL_00_PHYSICS_ENGINE_20260313T030502Z.md",
            "class_name": "V_Zoo_Zoo_E2_001",
            "predatory_gate": {"passed": True, "worst_dd_pct": 0.9, "trades": 9},
            "status": "ACTIVE"
        },
        "E2_002_VWAP_REVERSION": {
            "proposal": "PROPOSAL_00_PHYSICS_ENGINE_20260313T031742Z.md",
            "class_name": "ZOO_E2_002",
            "predatory_gate": {"passed": True, "worst_dd_pct": 0.0, "trades": 4},
            "status": "ACTIVE"
        }
    },
    "windows": {
        "SPRINT_15D": {
            "duration_days": 15,
            "purpose": "Fast iteration — surface bugs quickly, high signal density",
            "advancement_gate": "Sharpe >= 1.0, max DD <= 10%",
            "feeds_into": "SPRINT_30D parameters if passed"
        },
        "STANDARD_30D": {
            "duration_days": 30,
            "purpose": "Statistical significance — enough trades for Sharpe calculation",
            "advancement_gate": "Sharpe >= 1.5, max DD <= 12%",
            "feeds_into": "QUALIFYING_60D parameters if passed"
        },
        "QUALIFYING_60D": {
            "duration_days": 60,
            "purpose": "Regime exposure — likely to encounter at least one volatility shift",
            "advancement_gate": "Sharpe >= 2.0, max DD <= 14%",
            "feeds_into": "CP1_90D parameters if passed"
        },
        "CP1_90D": {
            "duration_days": 90,
            "purpose": "Constitutional CP1 qualification — the real test",
            "advancement_gate": "Per CHECKPOINTS.yaml: Sharpe >= 2.5, max DD <= 15%, 250+ trades",
            "feeds_into": "CP2_MICRO_CAPITAL if all gates passed"
        }
    },
    "data_extraction": {
        "per_trade": ["entry_time", "exit_time", "entry_price", "exit_price", "pnl", "hold_duration", "atr_at_entry", "regime_at_entry"],
        "per_day": ["daily_pnl", "cumulative_return", "rolling_sharpe_20d", "max_drawdown", "trade_count", "win_rate"],
        "per_window": ["total_return", "sharpe", "sortino", "max_drawdown", "calmar", "total_trades", "avg_hold_time", "regime_distribution"]
    },
    "notes": "All 4 windows start simultaneously for each strategy. Shorter windows produce results first, feeding parameter adjustments into longer windows. This is NOT sequential — it's parallel data extraction."
}

config_path = STATE_DIR / "paper_trading_matrix.json"
config_path.write_text(json.dumps(paper_trading_config, indent=2))
print(f"✅ THREAD 1: Paper trading matrix config → {config_path}")

# ══════════════════════════════════════════════════════════════════════════════
# THREAD 1 MISSION: Paper Trading Harness
# ══════════════════════════════════════════════════════════════════════════════

harness_content = """# MISSION: Paper Trading Harness — Multi-Window Runner
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_paper_trading_harness
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Two strategies survived the Predatory Gate (E2_001 Bollinger, E2_002 VWAP).
We need a harness that runs them in paper trading mode across 4 time windows
simultaneously, collecting granular data for the Champion Registry.

## BLUEPRINT
Create a PaperTradingHarness class that:
1. Reads state/paper_trading_matrix.json for strategy + window configs
2. Extracts strategy code from proposals (same extraction as Predatory Gate)
3. For each strategy × window combination, creates an independent instance
4. Each instance:
   - Loads historical + synthetic forward data
   - Runs the strategy bar-by-bar (simulating real-time)
   - Records per-trade data: entry/exit/pnl/hold_time/atr/regime
   - Records per-day data: daily_pnl/cumulative_return/rolling_sharpe
5. Writes results to state/paper_trades/{strategy}_{window}.json
6. Updates state/champion_registry.json with latest metrics
7. At window end: computes Sharpe, Sortino, max DD, total trades
8. Compares against the window's advancement gate
9. PASS/FAIL verdict written to state/paper_results_{window}.json

## DELIVERABLE
File: scripts/run_paper_trading.py

## CONSTRAINTS
- Must be runnable as: .venv/bin/python3 scripts/run_paper_trading.py
- Each strategy × window runs independently (can be killed without affecting others)
- All data written to state/ directory
- Read advancement gates from state/paper_trading_matrix.json
- No external API calls (uses synthetic forward data for now)
- No real money — CP1 is paper only
- Output valid Python only
"""
(MISSIONS_DIR / "mission_paper_trading_harness.md").write_text(harness_content)
missions.append({
    "id": "paper_trading_harness",
    "domain": "00_PHYSICS_ENGINE",
    "task": "implement_paper_trading_harness",
    "mission_file": "mission_paper_trading_harness.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 1,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 1: Paper trading across 4 time windows for data extraction",
})
print("✅ T1 Mission: Paper Trading Harness")

# ══════════════════════════════════════════════════════════════════════════════
# THREAD 2: STRATEGY FACTORY — Keep building while testing
# ══════════════════════════════════════════════════════════════════════════════

# E2.5: Resurrect E1 strategies with E2 lessons
resurrect_content = """# MISSION: E2.5 — Resurrect E1 Strategies With Graveyard Lessons
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_e1_resurrection
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
All 5 Epoch 1 strategies were killed in the Predatory Gate due to execution bugs:
- Chained indexing (bars['col'][cond] = val)
- Missing .loc[] usage
- Column name errors ('time' vs index)
- BaseStrategy vs Strategy import

Meanwhile, all Epoch 2 strategies that received Graveyard anti-pattern guidance survived.

## BLUEPRINT
For EACH of the 5 E1 strategy concepts, create a new FIXED implementation:
1. E2.5_001: Volatility Gatekeeper REBORN — ATR gate + EMA crossover
2. E2.5_002: Mean Reversion Sniper REBORN — VWAP + deviation entry
3. E2.5_003: Regime Chameleon REBORN — ADX regime switching (NO talib)
4. E2.5_004: Opening Range Breakout REBORN — first 30min range
5. E2.5_005: Momentum Decay Harvester REBORN — pullback after spike

Each reimplementation MUST:
- Inherit from Strategy (not BaseStrategy)
- Implement prepare_data(self, df, params, intelligence=None, vector_cache=None)
- Return DataFrame with entry_signal (bool), exit_signal (bool), ATR (float)
- Use .loc[] exclusively — NEVER chained indexing
- NEVER import talib
- Use parentheses around ALL boolean operations

Generate all 5 as a single proposal with clear class separation.

## DELIVERABLE
File: mantis_core/strategies/lab/epoch_2_5_resurrections.py

## CONSTRAINTS
- One file, 5 classes
- Each class must be independently testable
- No hardcoded parameters
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_e1_resurrection.md").write_text(resurrect_content)
missions.append({
    "id": "e1_resurrection_e2_5",
    "domain": "00_PHYSICS_ENGINE",
    "task": "implement_e1_resurrection",
    "mission_file": "mission_e1_resurrection.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 10,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 2: Resurrect killed E1 strategies with E2 Graveyard lessons",
})
print("✅ T2 Mission: E1 Resurrection (Epoch 2.5)")

# E3: Correlation/Pairs strategies — new topology
pairs_content = """# MISSION: Epoch 3 — Correlation/Pairs Strategy
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_correlation_strategy
TYPE: IMPLEMENTATION
VERSION: 1.0
EPOCH: 3

## CONTEXT
All existing Zoo strategies are single-instrument (MES only). A new topology:
correlation-based strategies that detect when MES deviates from a synthetic
moving benchmark and trades the reversion.

## BLUEPRINT
Create a SyntheticPairsStrategy that:
1. Computes a rolling correlation between MES close and its own 50-bar SMA
2. When correlation breaks below -0.5 (price diverges from trend), enter long
3. When correlation returns above 0.0 (convergence), exit
4. ATR-based position sizing (1 contract max)
5. No overnight, max 3 trades/day

This is a SELF-REFERENTIAL pairs trade: the "pair" is price vs its own trend.
No external data required.

## DELIVERABLE
File: mantis_core/strategies/lab/v_zoo_E3_001/v_zoo_E3_001_synthetic_pairs.py

## PHYSICS ENGINE CONSTRAINTS
- Inherit from Strategy, implement prepare_data()
- Return entry_signal, exit_signal, ATR
- .loc[] only, no talib, parentheses on booleans
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_e3_pairs.md").write_text(pairs_content)
missions.append({
    "id": "e3_001_synthetic_pairs",
    "domain": "00_PHYSICS_ENGINE",
    "task": "implement_correlation_strategy",
    "mission_file": "mission_e3_pairs.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 11,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 2: Epoch 3 new topology — correlation/pairs trading",
})
print("✅ T2 Mission: E3 Synthetic Pairs Strategy")

# ══════════════════════════════════════════════════════════════════════════════
# THREAD 3: INFRASTRUCTURE — Roadmap items that don't need live data
# ══════════════════════════════════════════════════════════════════════════════

# Auto-deploy pipeline
deploy_content = """# MISSION: Auto-Deploy Pipeline — Proposal to Target Path
DOMAIN: 03_ORCHESTRATION
TASK: implement_auto_deploy
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Current gap: the factory writes proposals to 08_IMPLEMENTATION_NOTES/ as markdown
containing Python code. After ratification, nothing extracts the code to its
declared DELIVERABLE path. Deployment is manual (sed extraction). This must be
automated.

## BLUEPRINT
Create an auto-deploy script that:
1. Scans 08_IMPLEMENTATION_NOTES/ for RATIFIED proposals
2. For each, reads the DELIVERABLE path from the proposal header
3. Extracts the Python code block (```python ... ```)
4. Writes it to the DELIVERABLE path
5. Validates the extracted code: syntax check (ast.parse), import check
6. Logs deployment to state/deployment_log.json
7. If DELIVERABLE path is in 04_GOVERNANCE/ → REFUSE (constitutional violation)
8. If code fails syntax check → REFUSE and log error

## DELIVERABLE
File: scripts/deploy_ratified.py

## CONSTRAINTS
- NEVER write to 04_GOVERNANCE/
- Must verify RATIFIED status before deploying
- Must ast.parse() before writing
- Idempotent — running twice produces same result
- Output valid Python only
"""
(MISSIONS_DIR / "mission_auto_deploy.md").write_text(deploy_content)
missions.append({
    "id": "auto_deploy_pipeline",
    "domain": "03_ORCHESTRATION",
    "task": "implement_auto_deploy",
    "mission_file": "mission_auto_deploy.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 5,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 3: Close the proposal→deployment gap",
})
print("✅ T3 Mission: Auto-Deploy Pipeline")

# Dashboard Data API
dashboard_content = """# MISSION: Dashboard Data API — Factory State Exporter
DOMAIN: 05_REPORTING
TASK: implement_dashboard_data_api
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Tamagotchi dashboard needs a data layer.
This module exports real-time factory state as structured JSON
that any frontend (web, E-Ink, voxel world) can consume.

## BLUEPRINT
Create a FactoryStateExporter class that reads:
1. orchestration/MISSION_QUEUE.json → mission status summary
2. orchestration/ORCHESTRATOR_STATE.json → run history
3. orchestration/VRAM_STATE.json → hardware utilization
4. state/champion_registry.json → strategy performance
5. state/predatory_gate_survivors.json → survivor list
6. state/paper_trading_matrix.json → active trading windows
7. docs/GRAVEYARD.md → failure count and latest entries

And produces a single dashboard_state.json containing:
- factory_status: IDLE / RUNNING / WAITING_RATIFICATION
- active_missions: count and names
- hardware: vram_used_pct, ram_used_pct, model_loaded
- strategies: total, active, dormant, killed
- paper_trading: per-window status and latest metrics
- graveyard_size: total entries
- version: current engine version
- uptime: time since last orchestrator start

## DELIVERABLE
File: 05_REPORTING/reporting_domain/factory_state_exporter.py

## CONSTRAINTS
- Read-only access to all state files
- Output must be valid JSON
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_dashboard_api.md").write_text(dashboard_content)
missions.append({
    "id": "dashboard_data_api",
    "domain": "05_REPORTING",
    "task": "implement_dashboard_data_api",
    "mission_file": "mission_dashboard_api.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 20,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 3: Tamagotchi data layer — factory state as JSON",
})
print("✅ T3 Mission: Dashboard Data API")

# Risk Manager
risk_content = """# MISSION: Real-Time Risk Manager
DOMAIN: 02_RISK_MANAGEMENT
TASK: implement_realtime_risk_manager
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Before paper trading goes live, we need a risk management layer that
monitors all active strategy instances and enforces position limits,
drawdown circuits, and correlation exposure caps in real time.

## BLUEPRINT
Create a RealTimeRiskManager class that:
1. Monitors all active paper trading instances
2. Enforces per-strategy limits:
   - max_contracts: 1
   - max_daily_loss: configurable (default $50)
   - max_drawdown_pct: from CHECKPOINTS.yaml
   - no_overnight: hard enforcement
3. Enforces portfolio-level limits:
   - max_total_exposure: 2 contracts across all strategies
   - max_correlated_exposure: if 2+ strategies signal same direction, cap at 1
   - daily_portfolio_loss_limit: $100
4. Circuit breakers:
   - If any strategy hits max_daily_loss → halt that strategy for the day
   - If portfolio hits daily limit → halt ALL strategies for the day
   - If max_drawdown breached → kill strategy and add to Graveyard
5. Logs all risk events to state/risk_events.json
6. Provides is_trade_allowed(strategy_id, direction, size) → bool

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/realtime_risk_manager.py

## CONSTRAINTS
- Fail CLOSED on any risk check failure
- Read limits from CHECKPOINTS.yaml
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_risk_manager_rt.md").write_text(risk_content)
missions.append({
    "id": "realtime_risk_manager",
    "domain": "02_RISK_MANAGEMENT",
    "task": "implement_realtime_risk_manager",
    "mission_file": "mission_risk_manager_rt.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 3,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "THREAD 3: Risk management must exist before paper trading goes live",
})
print("✅ T3 Mission: Real-Time Risk Manager")

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
MULTI-THREADED SPRINT — LOADED
{'='*60}

THREAD 1 — PAPER TRADING (runs in background):
  Config: state/paper_trading_matrix.json
  Mission: Paper Trading Harness (extracts + runs strategies)
  Windows: 15d / 30d / 60d / 90d (parallel, not sequential)
  Strategies: E2_001 Bollinger, E2_002 VWAP

THREAD 2 — STRATEGY FACTORY (keeps building):
  Mission: E1 Resurrection (5 strategies reborn with E2 lessons)
  Mission: E3 Synthetic Pairs (new correlation topology)
  → Survivors feed back into paper trading matrix

THREAD 3 — INFRASTRUCTURE (roadmap items):
  Mission: Auto-Deploy Pipeline (close proposal→target gap)
  Mission: Dashboard Data API (Tamagotchi data layer)
  Mission: Real-Time Risk Manager (must exist before live paper trading)

TOTAL NEW MISSIONS: {len(missions)} ({added} added to queue)

EXECUTION:
  git add -A && git commit -m "feat: multi-threaded sprint — paper trading + factory + infra in parallel"
  make drop
  python3 scripts/orchestrator_loop.py

AFTER FACTORY COMPLETES:
  1. Ratify proposals
  2. Deploy the paper trading harness:
     .venv/bin/python3 scripts/run_paper_trading.py
  3. Re-run Predatory Gate on E2.5 resurrections + E3 pairs
  4. Survivors join the paper trading matrix
  5. Factory keeps building while everything trades

THE SYSTEM NEVER STOPS PRODUCING.
""")
