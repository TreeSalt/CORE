# MISSION: Performance Reporter — CP1 Qualification Dashboard
DOMAIN: 05_REPORTING
TASK: implement_performance_reporter
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
Create a PerformanceReporter class that:
1. Reads state/trade_ledger.jsonl for trade history
2. Computes per-strategy and portfolio-level metrics:
   - Sharpe ratio (annualized), Sortino ratio
   - Max drawdown (%), Calmar ratio
   - Win rate, profit factor, avg win/loss ratio
   - Total trades, avg hold time, trades per day
3. Computes CP1 qualification status:
   - Days elapsed (need 90), Trades count (need 250)
   - Rolling 90d Sharpe (need >= 2.5), Max DD (need <= 15%)
4. Outputs a human-readable report to state/performance_report.md
5. Outputs machine-readable JSON to state/performance_report.json

## DELIVERABLE
File: 05_REPORTING/reporting_domain/performance_reporter.py

## CONSTRAINTS
- Read-only access to trade ledger
- No external API calls
- Output valid Python only
