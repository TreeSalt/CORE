# MISSION: Live Risk Monitor
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/live_risk_monitor.py

## REQUIREMENTS
- LiveRiskMonitor class
- check_drawdown(portfolio, max_dd_pct) -> bool: True if drawdown exceeds limit
- check_position_limit(position, max_qty) -> bool: True if position exceeds limit
- check_correlation(positions, max_corr) -> bool: True if portfolio correlation too high
- dead_man_switch(last_heartbeat_ts, max_seconds) -> bool: True if stale
- All methods are pure functions taking data in, returning bool
- No external calls of any kind
- Output valid Python only
