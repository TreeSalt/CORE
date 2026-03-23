# MISSION: Crypto Exchange Adapter
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_exchange_adapter.py

## REQUIREMENTS
- CryptoExchangeAdapter class with connect(), fetch_ohlcv(), disconnect()
- Normalize to {timestamp, open, high, low, close, volume}
- Support configurable symbols (BTC/USDT, ETH/USDT)
- Support timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Rate limiting: configurable max requests/min (default 10)
- Exponential backoff on errors
- Mock HTTP layer (no real API calls)
- Output valid Python only
