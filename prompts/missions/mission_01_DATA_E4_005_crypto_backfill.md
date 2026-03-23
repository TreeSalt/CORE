# MISSION: Crypto Historical Backfill
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_backfill.py

## REQUIREMENTS
- backfill(symbol, start_date, end_date, timeframe) -> list of candles
- Paginate through historical data respecting rate limits
- Save to data/crypto/{symbol}_{timeframe}.csv
- Resume capability: detect last saved timestamp, continue from there
- Validate downloaded data with crypto_normalizer
- No real API calls (stub the HTTP layer)
- Output valid Python only
