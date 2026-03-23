# MISSION: Strategy Correlation Guard
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
