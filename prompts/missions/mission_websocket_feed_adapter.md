# MISSION: WebSocket Feed Adapter
DOMAIN: 01_DATA_INGESTION
TASK: implement_websocket_feed_adapter
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
DATA_MULTIPLEXER needs real-time WebSocket adapter for market data feeds.

## BLUEPRINT
1. Connect to configurable WebSocket endpoint
2. Receive raw JSON, normalize to OHLCV DataFrame
3. Buffer and emit complete 5m bars via callback
4. Exponential backoff reconnect (1s→2s→4s→8s, max 60s)
5. Sovereign Ingestion (Art IV.7): validate data before downstream

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/websocket_feed_adapter.py

## CONSTRAINTS
- Use stdlib ssl (NOT websocket.SSLOpt — see GRAVEYARD)
- No hardcoded endpoints — read from config
- Fail closed on malformed data
- Output valid Python only
