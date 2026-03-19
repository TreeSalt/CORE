# Mission: 06_BENCH_E2_001_strategy_zoo_gate

## Domain
06_BENCHMARKING

## Model Tier
Sprint (9b)

## Description
Build a strategy zoo registration gate that validates trading strategies
before they enter the strategy zoo directory.

REQUIREMENTS:
1. Parse strategy Python file with ast module
2. Check: does it define required functions (generate_signals, run_strategy or equivalent)
3. Check: does it use only allowed imports (stdlib only, no pandas/numpy)
4. Check: does it include a docstring with strategy description
5. Check: does it handle empty/NaN price data without crashing
6. Return StrategyGateReport with pass/fail and findings

ALLOWED IMPORTS: ast, pathlib, typing, json, re
OUTPUT: 06_BENCHMARKING/benchmarking_domain/strategy_gate.py
TEST: Feed a valid strategy file -> PASS. Feed one missing generate_signals -> FAIL.
