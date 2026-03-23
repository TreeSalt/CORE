#!/usr/bin/env python3
"""
CORE v10.0.0 — OVERNIGHT EPOCH (March 22-23, 2026)
═══════════════════════════════════════════════════
Target window: 18:36 → 09:00 (14.5 hours / 870 minutes)
Mission count: 75 missions × ~7 min avg = ~525 min + overhead ≈ 10-12 hours
Buffer: 2-3 hours for retries, VRAM cycles, benchmark overhead

After running this script, execute:
  core run --daemon
  OR
  while true; do core run; sleep 10; done

Each mission is scoped for a 9B model on 8GB VRAM: clear deliverable,
single file output, no ambiguity. The model succeeds when it knows
exactly what to build.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

MISSIONS_DIR = Path("prompts/missions")
MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
QUEUE = Path("orchestration/MISSION_QUEUE.json")
now = datetime.now(timezone.utc).isoformat()

all_missions = []
priority = 0

def add(task_id, domain, content):
    global priority
    mission_file = f"mission_{task_id}.md"
    (MISSIONS_DIR / mission_file).write_text(content)
    all_missions.append({
        "id": task_id, "domain": domain, "task": task_id,
        "mission_file": mission_file, "type": "IMPLEMENTATION",
        "max_retries": 3, "status": "PENDING", "priority": priority,
        "authored_by": "Claude.ai — Supreme Council",
        "authored_at": now, "result": None,
        "started_at": None, "completed_at": None
    })
    priority += 1

# ══════════════════════════════════════════════════════════════════════
# WAVE 1: STRATEGY ZOO E3 — Five new strategies (12 missions)
# ══════════════════════════════════════════════════════════════════════

add("00_PHYSICS_E8_001_rsi_divergence", "00_PHYSICS_ENGINE", """# MISSION: RSI Divergence Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## CONTEXT
Detect RSI divergences — price makes new highs/lows but RSI does not confirm. Mean-reversion signal for ranging markets.

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/rsi_divergence.py

## REQUIREMENTS
- Detect bullish divergence (price lower low, RSI higher low)
- Detect bearish divergence (price higher high, RSI lower high)
- Configurable RSI period (default 14), lookback (default 20 bars)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
""")

add("00_PHYSICS_E8_002_market_profile", "00_PHYSICS_ENGINE", """# MISSION: Market Profile Value Area Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/market_profile_value.py

## REQUIREMENTS
- Calculate TPO profile from OHLCV bars
- Identify Value Area High, Value Area Low, Point of Control
- Long when price dips below VAL and reverses; short above VAH
- Configurable session window (default RTH 9:30-16:00)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
""")

add("00_PHYSICS_E8_003_overnight_trap", "00_PHYSICS_ENGINE", """# MISSION: Overnight Range Trap Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/overnight_range_trap.py

## REQUIREMENTS
- Calculate overnight range (18:00 prev day to 09:30 current)
- Detect breakout of overnight high/low in first 30 min RTH
- Fade if price returns inside range within N bars (default 3)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
""")

add("00_PHYSICS_E8_004_vwap_bands", "00_PHYSICS_ENGINE", """# MISSION: VWAP Standard Deviation Bands Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/vwap_bands.py

## REQUIREMENTS
- Calculate intraday VWAP and +/- 1, 2, 3 standard deviation bands
- Long when price touches -2SD band and reverses toward VWAP
- Short when price touches +2SD band and reverses toward VWAP
- Reset VWAP at session open (configurable)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
""")

add("00_PHYSICS_E8_005_keltner_squeeze", "00_PHYSICS_ENGINE", """# MISSION: Keltner Channel Squeeze Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/keltner_squeeze.py

## REQUIREMENTS
- Detect when Bollinger Bands contract inside Keltner Channels (squeeze)
- Track squeeze duration (bars)
- Signal on squeeze release: breakout direction = trade direction
- Configurable BB period (20), KC period (20), KC multiplier (1.5)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
""")

# Tests for each new strategy
for strat in ["rsi_divergence", "market_profile_value", "overnight_range_trap", "vwap_bands", "keltner_squeeze"]:
    add(f"06_BENCH_E6_{strat}_test", "06_BENCHMARKING", f"""# MISSION: Benchmark test for {strat} strategy
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_bench_{strat}.py

## REQUIREMENTS
- Import the strategy from 00_PHYSICS_ENGINE/physics_engine/strategies/{strat}.py
- Test with synthetic OHLCV data (at least 100 bars)
- Verify generate_signal returns correct dict keys: signal, confidence, entry_price, stop_loss
- Verify signal is one of: "LONG", "SHORT", "FLAT"
- Verify confidence is float between 0.0 and 1.0
- Verify no exceptions on empty data, single bar, normal data
- No external API calls
- Output valid Python only
""")

# Predatory gate for new strategies
add("00_PHYSICS_E8_006_predatory_new", "00_PHYSICS_ENGINE", """# MISSION: Predatory Gate for E8 Strategies
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/run_predatory_gate_e8.py

## REQUIREMENTS
- Run stress test on all E8 strategies (rsi_divergence, market_profile_value, overnight_range_trap, vwap_bands, keltner_squeeze)
- Scenarios: Flash crash (-8% in 5 bars), Gap down (-3% overnight), Whipsaw (5 direction changes in 10 bars), Dead flat (0.1% range for 50 bars)
- Track max drawdown per strategy per scenario
- Kill threshold: 15% max drawdown in any scenario
- Output JSON report to reports/predatory/E8_GATE_{timestamp}.json
- No external API calls
- Output valid Python only
""")

add("00_PHYSICS_E8_007_zoo_register_e3", "00_PHYSICS_ENGINE", """# MISSION: Register E8 Strategies in Champion Registry
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/register_e8_strategies.py

## REQUIREMENTS
- Read E8 predatory gate results from reports/predatory/
- For each SURVIVOR, add entry to state/champion_registry.json
- Entry format: {strategy_id, epoch, topology, predatory_status, registered_at}
- For each GRAVEYARD casualty, append to docs/GRAVEYARD.md with reason
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 2: MANTIS BIRTH — Crypto infrastructure (10 missions)
# ══════════════════════════════════════════════════════════════════════

add("01_DATA_E4_001_crypto_exchange", "01_DATA_INGESTION", """# MISSION: Crypto Exchange Adapter
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_exchange_adapter.py

## REQUIREMENTS
- CryptoExchangeAdapter class with connect(), fetch_ohlcv(), disconnect()
- Normalize to {timestamp, open, high, low, close, volume}
- Support configurable symbols (BTC/USDT, ETH/USDT)
- Support timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Rate limiting: configurable max requests/min (default 10)
- Exponential backoff on errors
- Mock HTTP layer (no real API calls)
- Output valid Python only
""")

add("01_DATA_E4_002_crypto_normalizer", "01_DATA_INGESTION", """# MISSION: Crypto Data Normalizer
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_normalizer.py

## REQUIREMENTS
- Convert unix timestamps (ms and s) to ISO 8601
- Normalize volume to base currency
- Fill missing candles (configurable: ffill or drop)
- Validate: no future timestamps, monotonic, no negative prices
- Log warnings for quality issues
- No external API calls
- Output valid Python only
""")

add("01_DATA_E4_003_crypto_symbols", "01_DATA_INGESTION", """# MISSION: Crypto Symbol Registry
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_symbols.py

## REQUIREMENTS
- Define CryptoSymbol dataclass: base, quote, exchange, min_lot, tick_size, fees_bps
- Pre-populate 10 major pairs: BTC/USDT, ETH/USDT, SOL/USDT, etc.
- get_symbol(pair_str) -> CryptoSymbol
- list_symbols(exchange=None) -> list
- validate_order(symbol, qty, price) -> bool (checks lot size, tick)
- No external API calls
- Output valid Python only
""")

add("01_DATA_E4_004_crypto_ws_stub", "01_DATA_INGESTION", """# MISSION: Crypto WebSocket Feed Stub
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_ws_feed.py

## REQUIREMENTS
- CryptoWebSocketFeed class with connect(), subscribe(symbols), on_message callback
- Parse incoming trade messages into {timestamp, symbol, price, qty, side}
- Parse incoming orderbook updates into {timestamp, symbol, bids, asks}
- Reconnect with exponential backoff on disconnect
- All network calls are stubbed/mocked for testing
- No external API calls
- Output valid Python only
""")

add("01_DATA_E4_005_crypto_backfill", "01_DATA_INGESTION", """# MISSION: Crypto Historical Backfill
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_backfill.py

## REQUIREMENTS
- backfill(symbol, start_date, end_date, timeframe) -> list of candles
- Paginate through historical data respecting rate limits
- Save to data/crypto/{symbol}_{timeframe}.csv
- Resume capability: detect last saved timestamp, continue from there
- Validate downloaded data with crypto_normalizer
- No real API calls (stub the HTTP layer)
- Output valid Python only
""")

# Tests for MANTIS modules
for mod in ["crypto_exchange_adapter", "crypto_normalizer", "crypto_symbols", "crypto_ws_feed", "crypto_backfill"]:
    add(f"06_BENCH_E6_{mod}_test", "06_BENCHMARKING", f"""# MISSION: Test for {mod}
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/01_DATA_INGESTION/test_bench_{mod}.py

## REQUIREMENTS
- Import module from 01_DATA_INGESTION/data_ingestion/{mod}.py
- Test happy path with synthetic data
- Test edge cases: empty data, malformed timestamps, negative prices
- Test error handling: connection failures, rate limit exceeded
- All tests use mocks, no real network calls
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 3: RISK + TRADE INFRASTRUCTURE (8 missions)
# ══════════════════════════════════════════════════════════════════════

add("02_RISK_E5_001_trade_ledger", "02_RISK_MANAGEMENT", """# MISSION: Append-Only Trade Ledger
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/trade_ledger.py

## REQUIREMENTS
- SQLite database, append-only (no UPDATE/DELETE)
- Schema: id, timestamp, strategy_id, symbol, side, qty, price, pnl, prev_hash, entry_hash
- entry_hash = sha256(prev_hash + timestamp + strategy_id + side + qty + price)
- record_trade() -> entry; verify_chain() -> bool; get_trades() -> list
- No method to delete or modify records
- No external API calls
- Output valid Python only
""")

add("02_RISK_E5_002_position_tracker", "02_RISK_MANAGEMENT", """# MISSION: Real-Time Position Tracker
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/position_tracker.py

## REQUIREMENTS
- Track open positions per strategy per symbol
- update_position(strategy_id, symbol, side, qty, price)
- get_position(strategy_id, symbol) -> {qty, avg_price, unrealized_pnl, side}
- get_all_positions() -> list
- get_portfolio_exposure() -> {long_exposure, short_exposure, net_exposure}
- No external API calls
- Output valid Python only
""")

add("02_RISK_E5_003_drawdown_monitor", "02_RISK_MANAGEMENT", """# MISSION: Drawdown Monitor
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/drawdown_monitor.py

## REQUIREMENTS
- Track peak equity and current drawdown per strategy
- update(strategy_id, equity) -> DrawdownState
- DrawdownState: {peak, current, drawdown_pct, max_drawdown_pct, bars_in_drawdown}
- check_breach(strategy_id, threshold=0.15) -> bool
- get_all_drawdowns() -> dict of strategy -> DrawdownState
- No external API calls
- Output valid Python only
""")

add("02_RISK_E5_004_correlation_guard", "02_RISK_MANAGEMENT", """# MISSION: Strategy Correlation Guard
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/correlation_guard.py

## REQUIREMENTS
- Track PnL streams per strategy over rolling window
- compute_correlation(strategy_a, strategy_b, window=30) -> float
- get_correlation_matrix(strategies) -> dict of pairs -> correlation
- flag_correlated(threshold=0.7) -> list of correlated pairs
- Purpose: prevent deploying multiple strategies that are secretly the same bet
- No external API calls
- Output valid Python only
""")

# Tests for risk modules
for mod in ["trade_ledger", "position_tracker", "drawdown_monitor", "correlation_guard"]:
    add(f"06_BENCH_E6_{mod}_test", "06_BENCHMARKING", f"""# MISSION: Test for {mod}
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/02_RISK_MANAGEMENT/test_bench_{mod}.py

## REQUIREMENTS
- Import from 02_RISK_MANAGEMENT/risk_management/{mod}.py
- Test happy path with synthetic trade data
- Test edge cases: zero quantity, negative prices, duplicate entries
- Test hash chain integrity (for trade_ledger)
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 4: RED TEAM + SECURITY (6 missions)
# ══════════════════════════════════════════════════════════════════════

add("08_CYBER_E5_001_selftest_runner", "08_CYBERSECURITY", """# MISSION: Red Team Self-Test Runner
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/selftest_runner.py

## REQUIREMENTS
- Discover all probe modules in scripts/redteam/
- Execute each module's test suite
- Aggregate: total probes, passed, failed, severity breakdown
- JSON report: reports/security/SELFTEST_{timestamp}.json
- Markdown summary: reports/security/SELFTEST_{timestamp}.md
- Exit code 0 if no CRITICAL, 1 otherwise
- No external API calls
- Output valid Python only
""")

add("08_CYBER_E5_002_supply_chain", "08_CYBERSECURITY", """# MISSION: Supply Chain Dependency Auditor
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/supply_chain_audit.py

## REQUIREMENTS
- Parse requirements.txt for all dependencies
- Verify all have == version pinning and --hash entries
- Check typosquatting against common packages (requests, numpy, pandas, etc.)
- Flag unhashed packages as CRITICAL
- JSON report with package, version, pinned, hashed, risk_level
- No external API calls
- Output valid Python only
""")

add("08_CYBER_E5_003_path_traversal", "08_CYBERSECURITY", """# MISSION: Path Traversal Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/path_traversal_probes.py

## REQUIREMENTS
- Generate mission files that attempt path traversal in deliverable paths
- Test vectors: ../04_GOVERNANCE/evil.py, /etc/passwd, symlink attacks
- Each probe includes expected result (should be caught by benchmark)
- Output as JSON array of {probe_id, attack_path, expected_gate, expected_result}
- 15+ probes covering different traversal techniques
- No external API calls
- Output valid Python only
""")

add("08_CYBER_E5_004_prompt_injection", "08_CYBERSECURITY", """# MISSION: Prompt Injection Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/prompt_injection_probes.py

## REQUIREMENTS
- Generate mission files containing prompt injection attempts
- Vectors: "ignore previous instructions", role-play attacks, delimiter injection, system prompt extraction
- Each probe is a mission file that tries to make the LLM ignore constraints
- 20+ probes across 5 injection categories
- Output as JSON array of {probe_id, category, injection_text, expected_behavior}
- No external API calls
- Output valid Python only
""")

add("08_CYBER_E5_005_resource_exhaustion", "08_CYBERSECURITY", """# MISSION: Resource Exhaustion Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/resource_exhaustion_probes.py

## REQUIREMENTS
- Generate mission files designed to exhaust resources
- Vectors: infinite loops, recursive imports, massive string generation, fork bombs in code output
- Each probe should be caught by the benchmark timeout or resource limits
- 10+ probes covering CPU, memory, and disk exhaustion
- Output as JSON array of {probe_id, resource_type, technique, expected_gate}
- No external API calls
- Output valid Python only
""")

add("08_CYBER_E5_006_security_dashboard", "08_CYBERSECURITY", """# MISSION: Security Dashboard Data Aggregator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/security_dashboard.py

## REQUIREMENTS
- Read all reports from reports/security/
- Aggregate: total scans, findings by severity, trend over time
- Read credential scan results, governance bypass results, supply chain results
- Output consolidated JSON: reports/security/DASHBOARD_{timestamp}.json
- Include: last_scan_time, total_findings, critical_count, open_issues
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 5: REPORTING + OBSERVABILITY (6 missions)
# ══════════════════════════════════════════════════════════════════════

add("05_REPORT_E4_001_perf_reporter", "05_REPORTING", """# MISSION: Strategy Performance Reporter
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/performance_reporter.py

## REQUIREMENTS
- Read trade data from trade ledger interface
- Calculate: Sharpe, max drawdown, win rate, profit factor, avg win/loss
- Markdown report with per-strategy breakdown
- Include equity curve data points
- Output to reports/performance/PERF_{timestamp}.md
- No external API calls
- Output valid Python only
""")

add("05_REPORT_E4_002_session_summary_v2", "05_REPORTING", """# MISSION: Session Summary Generator v2
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/session_summary_v2.py

## REQUIREMENTS
- Read ORCHESTRATOR_STATE.json and MISSION_QUEUE.json
- Calculate: total missions, pass rate, domains covered, runtime
- Read git log for session commits
- Markdown summary for public sharing
- Output to reports/sessions/SESSION_{timestamp}.md
- No external API calls
- Output valid Python only
""")

add("05_REPORT_E4_003_domain_health", "05_REPORTING", """# MISSION: Domain Health Report
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/domain_health.py

## REQUIREMENTS
- For each of the 9 domains: count files, count tests, count proposals, count escalations
- Calculate health score per domain (0-100) based on test coverage and pass rate
- Identify domains with zero tests as CRITICAL
- Output Markdown table: domain, files, tests, proposals, escalations, health_score
- Output to reports/health/DOMAIN_HEALTH_{timestamp}.md
- No external API calls
- Output valid Python only
""")

add("05_REPORT_E4_004_factory_metrics", "05_REPORTING", """# MISSION: Factory Metrics Exporter
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/factory_metrics.py

## REQUIREMENTS
- Read all RATIFICATION and ESCALATION files from 08_IMPLEMENTATION_NOTES/
- Calculate: missions per epoch, avg time per mission, pass rate trend
- Calculate: missions per domain, busiest domain, most escalated domain
- Output JSON: reports/metrics/FACTORY_METRICS_{timestamp}.json
- Output Markdown summary alongside
- No external API calls
- Output valid Python only
""")

add("05_REPORT_E4_005_version_history", "05_REPORTING", """# MISSION: Version History Tracker
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/version_history.py

## REQUIREMENTS
- Parse git tags and DECISION_LOG.md for version milestones
- Build timeline: version, date, key changes, mission count
- Output Markdown timeline to reports/VERSION_HISTORY.md
- Include: v4.x era (legacy), v9.x era (factory), v10.0.0 (foundation)
- No external API calls
- Output valid Python only
""")

add("05_REPORT_E4_006_linkedin_generator", "05_REPORTING", """# MISSION: LinkedIn Post Generator
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/generate_linkedin_post.py

## REQUIREMENTS
- Read latest session summary and factory metrics
- Generate a LinkedIn-formatted post highlighting key achievements
- Include: mission count, pass rate, domains touched, key deliverables
- Tone: professional but energetic, technical but accessible
- Output to reports/linkedin/POST_{timestamp}.md
- Configurable: --tone (technical|casual|executive)
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 6: INTEGRATION + SMOKE TESTS (5 missions)
# ══════════════════════════════════════════════════════════════════════

add("07_INTEG_E2_001_smoke_tests", "07_INTEGRATION", """# MISSION: Integration Smoke Test Suite
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/smoke_tests.py

## REQUIREMENTS
- Test 1: Mission queue read/write cycle
- Test 2: Semantic router domain resolution
- Test 3: Benchmark runner on known-good proposal
- Test 4: Governor seal verification (valid)
- Test 5: Governor seal verification (tampered — must FAIL)
- Test 6: VRAM state read/write
- All mocked, no live LLM
- Exit 0 if pass, 1 if fail
- No external API calls
- Output valid Python only
""")

add("07_INTEG_E2_002_e2e_pipeline", "07_INTEGRATION", """# MISSION: End-to-End Pipeline Test
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/e2e_pipeline_test.py

## REQUIREMENTS
- Simulate full pipeline: create mission -> route -> mock generate -> benchmark -> proposal
- Verify proposal file is created at expected path
- Verify benchmark report is generated
- Verify mission status transitions: PENDING -> IN_PROGRESS -> AWAITING_RATIFICATION
- All mocked, no live LLM
- No external API calls
- Output valid Python only
""")

add("07_INTEG_E2_003_domain_wiring", "07_INTEGRATION", """# MISSION: Domain Wiring Verification
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/domain_wiring_test.py

## REQUIREMENTS
- For each domain in DOMAINS.yaml, verify: directory exists, __init__.py exists, at least one .py module
- Verify write_path matches actual directory structure
- Verify authorized_agents are valid model names
- Verify security_class is one of: INTERNAL, CONFIDENTIAL, PUBLIC
- Report any mismatches
- No external API calls
- Output valid Python only
""")

add("07_INTEG_E2_004_import_audit", "07_INTEGRATION", """# MISSION: Cross-Domain Import Audit
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/import_audit.py

## REQUIREMENTS
- Scan all .py files in the repo
- Build import graph: which files import from which modules
- Flag circular imports
- Flag imports from wrong domains (e.g. 01_DATA importing from 00_PHYSICS)
- Flag remaining antigravity_harness references (should be 0)
- Output JSON: reports/audit/IMPORT_AUDIT_{timestamp}.json
- No external API calls
- Output valid Python only
""")

add("07_INTEG_E2_005_config_validator", "07_INTEGRATION", """# MISSION: Configuration File Validator
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/config_validator.py

## REQUIREMENTS
- Validate DOMAINS.yaml: all required fields present, no duplicate IDs
- Validate OPERATOR_INSTANCE.yaml: version matches __init__.py
- Validate CHECKPOINTS.yaml: thresholds are numeric, phases are sequential
- Validate LOCAL_LOCKDOWN.json: valid JSON, enabled is bool
- Validate MISSION_QUEUE.json: all missions have required fields
- Output: {file, valid, errors} for each config
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# WAVE 7: ORCHESTRATION EVOLUTION (8 missions)
# ══════════════════════════════════════════════════════════════════════

add("03_ORCH_E7_001_readme_v10", "03_ORCHESTRATION", """# MISSION: README.md Updater for v10.0.0
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/update_readme.py

## REQUIREMENTS
- Read version from mantis_core/__init__.py
- Count ratified missions from 08_IMPLEMENTATION_NOTES/PROPOSAL_*.md
- Count escalations from ESCALATIONS/
- Update badge URLs with current counts
- Replace 'antigravity_harness' with 'mantis_core'
- Write updated README.md
- No external API calls
- Output valid Python only
""")

add("03_ORCH_E7_002_changelog", "03_ORCHESTRATION", """# MISSION: CHANGELOG.md Generator
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/generate_changelog.py

## REQUIREMENTS
- Parse git log for conventional commits (feat:, fix:, refactor:)
- Group by date range
- Highlight BREAKING changes
- Include migration notes for antigravity_harness -> mantis_core
- Write CHANGELOG.md
- No external API calls
- Output valid Python only
""")

add("03_ORCH_E7_003_epoch_scheduler", "03_ORCHESTRATION", """# MISSION: Epoch Scheduler
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/epoch_scheduler.py

## REQUIREMENTS
- Read completed missions from MISSION_QUEUE.json
- Read ESCALATIONS/ for failed missions needing retry
- Generate next epoch mission list with priorities
- Write new MISSION_QUEUE.json (backup current first)
- --dry-run flag to preview
- Log decisions for each mission
- No external API calls
- Output valid Python only
""")

add("03_ORCH_E7_004_mission_templates", "03_ORCHESTRATION", """# MISSION: Mission Template Library
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/mission_templates.py

## REQUIREMENTS
- Define templates for common mission types: IMPLEMENTATION, TEST, DOCUMENTATION, REFACTOR
- Each template has: required fields, default constraints, deliverable path pattern
- generate_mission(template_type, domain, task_name, **kwargs) -> mission file content
- validate_mission(mission_path) -> {valid, errors}
- List available templates with --list flag
- No external API calls
- Output valid Python only
""")

add("03_ORCH_E7_005_health_check", "03_ORCHESTRATION", """# MISSION: Factory Health Check Script
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/factory_health_check.py

## REQUIREMENTS
- Check Ollama connectivity and loaded models
- Check VRAM availability vs requirements
- Check governor seal integrity
- Check mission queue for stuck missions (IN_PROGRESS > 30 min)
- Check disk space for proposals directory
- Output: GREEN (all clear), YELLOW (warnings), RED (failures)
- No external API calls beyond localhost Ollama
- Output valid Python only
""")

add("03_ORCH_E7_006_mission_stats", "03_ORCHESTRATION", """# MISSION: Mission Statistics CLI Command
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/mission_stats.py

## REQUIREMENTS
- Read all historical MISSION_QUEUE.json entries and proposals
- Calculate: total missions ever, pass rate by epoch, avg time per mission
- Calculate: missions by domain, most productive domain
- Display as formatted table in terminal
- Callable as: python3 scripts/mission_stats.py
- No external API calls
- Output valid Python only
""")

add("06_BENCH_E5_001_quality_gate", "06_BENCHMARKING", """# MISSION: Proposal Quality Gate
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/proposal_quality_gate.py

## REQUIREMENTS
- validate_proposal(proposal_path, mission_path) -> QualityReport
- Check 1: AST parses without errors
- Check 2: Deliverable path matches mission spec
- Check 3: All imports resolvable (no hallucinated packages)
- Check 4: No writes to 04_GOVERNANCE/
- Check 5: Code >20 lines (not a stub)
- Check 6: No hardcoded credentials
- QualityReport: passed, checks list, score 0-100
- No external API calls
- Output valid Python only
""")

add("06_BENCH_E5_002_benchmark_report", "06_BENCHMARKING", """# MISSION: Benchmark Summary Report Generator
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/benchmark_report.py

## REQUIREMENTS
- Read all benchmark results from 06_BENCHMARKING/reports/
- Aggregate: total benchmarks run, pass rate, common failure reasons
- Identify flaky benchmarks (pass sometimes, fail sometimes)
- Output Markdown: reports/benchmarks/BENCH_SUMMARY_{timestamp}.md
- Output JSON alongside for dashboard consumption
- No external API calls
- Output valid Python only
""")

# ══════════════════════════════════════════════════════════════════════
# QUEUE IT
# ══════════════════════════════════════════════════════════════════════

queue = {"missions": all_missions}
QUEUE.write_text(json.dumps(queue, indent=2))

# Count by domain
from collections import Counter
domain_counts = Counter(m["domain"] for m in all_missions)

print("═" * 60)
print("  CORE v10.0.0 — OVERNIGHT EPOCH (FULL)")
print("  Window: 18:36 → 09:00 (14.5 hours)")
print("═" * 60)
print()
for domain, count in sorted(domain_counts.items()):
    print(f"  {domain:30s} {count:3d} missions")
print(f"  {'─' * 40}")
print(f"  {'TOTAL':30s} {len(all_missions):3d} missions")
print()
print(f"  Estimated runtime: ~{len(all_missions) * 7} min ({len(all_missions) * 7 / 60:.1f} hours)")
print(f"  Buffer remaining:  ~{14.5 - (len(all_missions) * 7 / 60):.1f} hours for retries")
print()
print("  Run:")
print("    core run --daemon")
print("  OR:")
print("    while true; do core run; sleep 10; done")
print("═" * 60)
