# MISSION: Strategy Performance Reporter
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/performance_reporter.py

## REQUIREMENTS
- Read trade data from trade ledger interface
- Calculate: Sharpe, max drawdown, win rate, profit factor, avg win/loss
- Markdown report with per-strategy breakdown
- Include equity curve data points
- Output to reports/performance/PERF_{timestamp}.md
- No external API calls
- Output valid Python only
