# MISSION: Real-Time Position Tracker
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
