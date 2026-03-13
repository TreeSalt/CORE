# MISSION: Champion Registry
DOMAIN: 05_REPORTING
TASK: implement_champion_registry
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
1. JSON registry at state/champion_registry.json
2. Register strategies with: ID, epoch, entry_date, params
3. Update daily P&L, cumulative return, Sharpe, max drawdown
4. Compute rankings across all active strategies
5. Flag strategies breaching CHECKPOINTS.yaml drawdown threshold
6. Append-only history

## DELIVERABLE
File: 05_REPORTING/reporting_domain/champion_registry.py

## CONSTRAINTS
- JSON append-only for history
- Rankings recomputed on every update
- No external API calls
- Output valid Python only
