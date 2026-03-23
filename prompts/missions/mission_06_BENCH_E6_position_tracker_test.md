# MISSION: Test for position_tracker
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/02_RISK_MANAGEMENT/test_bench_position_tracker.py

## REQUIREMENTS
- Import from 02_RISK_MANAGEMENT/risk_management/position_tracker.py
- Test happy path with synthetic trade data
- Test edge cases: zero quantity, negative prices, duplicate entries
- Test hash chain integrity (for trade_ledger)
- No external API calls
- Output valid Python only
