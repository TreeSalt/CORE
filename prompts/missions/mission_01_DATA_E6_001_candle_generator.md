# MISSION: Synthetic Candle Generator
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/candle_generator.py

## REQUIREMENTS
- generate_trending(n, start_price, drift_pct, noise_pct) -> list of candle dicts
- generate_mean_reverting(n, center_price, amplitude_pct, noise_pct) -> list of candle dicts
- generate_volatile(n, start_price, volatility_pct) -> list of candle dicts
- generate_flash_crash(n, start_price, crash_bar, crash_pct, recovery_bars) -> list of candle dicts
- Each candle has: timestamp, open, high, low, close, volume
- Uses random module with configurable seed for reproducibility
- No external calls
- Output valid Python only
