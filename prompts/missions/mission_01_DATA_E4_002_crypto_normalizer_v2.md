# MISSION: Crypto Data Normalizer
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_normalizer.py

## REQUIREMENTS
- normalize_timestamps(candles, input_format) -> list: convert unix ms/s to ISO 8601
- normalize_volume(candles, denomination) -> list: convert quote volume to base volume
- fill_gaps(candles, method) -> list: method is "ffill" or "drop"
- validate_integrity(candles) -> dict: check no future timestamps, monotonic, no negatives
- All functions are pure — take data in, return data out, no side effects
- Log warnings via Python logging module for data quality issues
- No external calls of any kind
- Output valid Python only
