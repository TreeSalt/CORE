# MISSION: Crypto WebSocket Feed Stub
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_ws_feed.py

## REQUIREMENTS
- CryptoWebSocketFeed class
- connect(config: dict) method — accepts dictionary with connection settings
- subscribe(symbols_list: list) method
- on_message(callback) method
- Parse trade messages into dict: {timestamp, symbol, price, qty, side}
- Parse orderbook updates into dict: {timestamp, symbol, bids, asks}
- Reconnect logic with configurable backoff parameters
- ALL network operations are no-ops returning mock data — this is a stub only
- No external calls of any kind
- Output valid Python only
