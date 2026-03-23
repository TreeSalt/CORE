# MISSION: Crypto Historical Backfill
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_backfill.py

## REQUIREMENTS
- backfill(adapter, symbol, start_date, end_date, timeframe) -> list of candle dicts
- Takes an adapter instance as first argument — never creates its own connections
- Paginate through date range respecting rate limits from adapter
- Save results to CSV at a caller-specified output_path
- Resume capability: detect last saved timestamp, continue from there
- Validate downloaded data using normalizer validate_integrity function
- All actual network calls delegated to the adapter (which is stubbed)
- No external calls of any kind
- Output valid Python only
