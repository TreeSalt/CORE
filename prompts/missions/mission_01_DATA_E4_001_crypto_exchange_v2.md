# MISSION: Crypto Exchange Adapter
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_exchange_adapter.py

## REQUIREMENTS
- CryptoExchangeAdapter class
- connect(config: dict) method — accepts a dictionary with connection settings
- fetch_ohlcv(symbol: str, timeframe: str) method — returns list of candle dicts
- disconnect() method
- Each candle dict has: timestamp, open, high, low, close, volume
- Supported symbols: "BTC_USDT", "ETH_USDT", "SOL_USDT"
- Supported timeframes: "1m", "5m", "15m", "1h", "4h", "1d"
- Rate limiting via configurable max_requests_per_minute (int)
- Exponential backoff on errors with max_retries parameter
- ALL network calls return synthetic mock data from _generate_mock_candle()
- No string literals containing dots or slashes that resemble addresses
- No external calls of any kind
- Output valid Python only
