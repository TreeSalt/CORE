# MISSION: Real-Time Risk Manager
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
