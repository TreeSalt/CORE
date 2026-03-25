# MISSION: Candle Generator Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/01_DATA_INGESTION/test_candle_generator.py

## REQUIREMENTS
- test_trending_up_has_positive_drift: verify last close > first close for positive drift
- test_mean_reverting_stays_near_center: verify prices stay within amplitude of center
- test_flash_crash_drops: verify a candle at crash_bar has close significantly below start
- test_candle_fields_present: verify each candle has timestamp, open, high, low, close, volume
- test_reproducible_with_seed: verify two runs with same seed produce identical candles
- Use pytest
- No external calls
- Output valid Python only
