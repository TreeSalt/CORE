# MISSION: Crypto WebSocket Feed Stub
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_ws_feed.py

## REQUIREMENTS
- CryptoWebSocketFeed class with connect(), subscribe(symbols), on_message callback
- Parse incoming trade messages into {timestamp, symbol, price, qty, side}
- Parse incoming orderbook updates into {timestamp, symbol, bids, asks}
- Reconnect with exponential backoff on disconnect
- All network calls are stubbed/mocked for testing
- No external API calls
- Output valid Python only
