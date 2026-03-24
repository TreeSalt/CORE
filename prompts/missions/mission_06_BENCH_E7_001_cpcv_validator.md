# MISSION: Combinatorial Purged Cross-Validation Engine
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking/cpcv_validator.py

## REQUIREMENTS
- generate_splits(n_groups, k_test) -> list of (train_indices, test_indices) tuples
- purge(train_idx, test_idx, pred_times, eval_times) -> filtered train_idx
- embargo(train_idx, test_idx, embargo_bars) -> filtered train_idx
- run_cpcv(data, strategy_fn, n_groups, k_test, embargo_bars) -> dict with per-path sharpe, variance, mean
- All functions are pure — take data in, return results
- No external calls
- Output valid Python only
