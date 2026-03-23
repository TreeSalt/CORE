# MISSION: Benchmark test for market_profile_value strategy
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_bench_market_profile_value.py

## REQUIREMENTS
- Import the strategy from 00_PHYSICS_ENGINE/physics_engine/strategies/market_profile_value.py
- Test with synthetic OHLCV data (at least 100 bars)
- Verify generate_signal returns correct dict keys: signal, confidence, entry_price, stop_loss
- Verify signal is one of: "LONG", "SHORT", "FLAT"
- Verify confidence is float between 0.0 and 1.0
- Verify no exceptions on empty data, single bar, normal data
- No external API calls
- Output valid Python only
