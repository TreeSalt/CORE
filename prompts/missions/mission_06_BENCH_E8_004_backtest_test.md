# MISSION: Backtest Engine Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_backtest_engine.py

## REQUIREMENTS
- test_run_returns_metrics: verify run() returns dict with total_return, sharpe_ratio, max_drawdown
- test_no_trades_when_no_signal: verify a strategy that never signals produces zero trades
- test_equity_curve_length: verify equity curve has same length as input candles
- test_initial_cash_preserved_on_empty: verify portfolio equals initial cash with no trades
- Use pytest
- No external calls
- Output valid Python only
