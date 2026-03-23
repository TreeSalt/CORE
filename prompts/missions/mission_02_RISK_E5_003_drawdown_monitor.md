# MISSION: Drawdown Monitor
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
