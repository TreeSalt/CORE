# MISSION: Backtest Engine
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/backtest_engine.py

## REQUIREMENTS
- BacktestEngine class
- load_candles(csv_path) -> list of candle dicts
- run(strategy, candles, initial_cash) -> dict with trades, equity_curve, metrics
- Metrics: total_return, sharpe_ratio, max_drawdown, win_rate, num_trades
- Uses paper_trade_harness internally for order execution
- No look-ahead bias: strategy sees only past candles at each step
- No external network calls
- Output valid Python only
