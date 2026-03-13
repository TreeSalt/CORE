# MISSION: Paper Trading Harness — Multi-Window Runner
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
