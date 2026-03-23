# MISSION: Crypto Data Normalizer
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_normalizer.py

## REQUIREMENTS
- Convert unix timestamps (ms and s) to ISO 8601
- Normalize volume to base currency
- Fill missing candles (configurable: ffill or drop)
- Validate: no future timestamps, monotonic, no negative prices
- Log warnings for quality issues
- No external API calls
- Output valid Python only
