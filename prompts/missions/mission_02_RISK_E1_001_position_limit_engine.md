# Mission: Position Limit Engine — Per-Strategy and Portfolio-Level Caps

## Domain
02_RISK_MANAGEMENT

## Model Tier
Sprint (9b)

## Description
Build a position limit engine that enforces per-strategy and portfolio-level
risk caps.

REQUIREMENTS:
- Configurable max position size per strategy (dollars and shares)
- Configurable max portfolio exposure (total across all strategies)
- Configurable max single-name concentration (% of portfolio in one ticker)
- Returns ALLOW/DENY for proposed trades with denial reason
- Logs all decisions to audit trail

OUTPUT: 02_RISK_MANAGEMENT/position_limit_engine.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, datetime, math
TEST: Set portfolio max to $10,000. Submit trade for $5,000 → ALLOW. Submit second trade for $6,000 → DENY (exceeds portfolio max). Assert denial reason contains "portfolio limit".

## Acceptance Criteria
- RiskConfig dataclass with per_strategy_max, portfolio_max, concentration_max
- evaluate_trade(trade, current_positions, config) returns TradeDecision
- TradeDecision has allowed bool and reason string
- Logs decisions to JSON audit file
- Handles empty portfolio (first trade always allowed if under limits)
