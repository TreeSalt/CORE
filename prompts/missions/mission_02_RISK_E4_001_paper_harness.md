# MISSION: Paper Trading Harness
DOMAIN: 02_RISK_MANAGEMENT
TASK: implement_paper_trading_harness
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0 Phase 1C/2C: Deploy a paper trading harness that runs champion strategies against live (delayed) market data. Each strategy runs in its own thread with independent PnL tracking. No real capital.

## DELIVERABLE
File: scripts/run_paper_trading.py

## REQUIREMENTS
- Load strategies from state/champion_registry.json
- Run each in separate thread with simulated execution
- Track per-strategy PnL, trades, max drawdown in real-time
- Write results to reports/paper_trading/
- Constitutional constraint: max_drawdown hard stop at 15%
- Configurable time windows (15d, 30d, 60d, 90d)
- No real brokerage connections
- No external API calls beyond market data
- Output valid Python only
