# Mission: 02_RISK_E3_001_walk_forward

## Domain
02_RISK_MANAGEMENT

## Model Tier
Sprint (9b)

## Description
Build a walk-forward testing framework that validates strategies on unseen data.

CONTEXT: Backtesting on historical data produces strategies optimized for the past.
Walk-forward splits data into rolling train and test windows:
  Window 1: train on rows 0-299, test on rows 300-399
  Window 2: train on rows 100-399, test on rows 400-499
  Window 3: train on rows 200-499, test on rows 500-599
If the strategy is profitable across most test windows it has real edge.

REQUIREMENTS:
1. split_walk_forward(data_rows, train_size, test_size, step_size) — returns list of (train_rows, test_rows) tuples
2. run_walk_forward(strategy_func, all_rows, train_size, test_size, step_size) — runs strategy.run_backtest on each test window and collects results
3. aggregate_results(window_results) — computes: avg_return, worst_window_return, best_window_return, consistency_score
   consistency_score = number of profitable windows divided by total windows
4. A strategy passes if consistency_score >= 0.6

strategy_func must accept (ohlcv_rows, initial_balance) and return an object with total_return attribute.

ALLOWED IMPORTS: statistics, math, dataclasses, typing, pathlib, json, csv
NO EXTERNAL DEPENDENCIES.
OUTPUT: 02_RISK_MANAGEMENT/walk_forward.py
TEST: Create 1000 rows of synthetic uptrending data. Split with train=200 test=100 step=100. Assert at least 5 windows. Assert consistency_score is a float between 0 and 1.
