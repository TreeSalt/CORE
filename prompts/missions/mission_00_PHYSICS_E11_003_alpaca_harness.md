# MISSION: MANTIS Alpaca Paper Trading Harness
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E11_003_alpaca_harness
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
MANTIS must trade BTC/USD on Alpaca paper trading. API credentials are in env vars
ALPACA_API_KEY and ALPACA_SECRET_KEY. This harness bridges signals to orders.
Fail-closed: any error = no order, never a rogue order.

## BLUEPRINT
1. Connection: read keys from env, base URL paper-api.alpaca.markets, health check
2. Data: fetch BTC/USD OHLCV bars (1Min to 1Day timeframes), return as float lists
3. Orders: submit market orders, verify fills, log to state/mantis_trade_log.json
4. Positions: query current position, equity, buying power as PositionSnapshot
5. Safety: max 0.01 BTC default, never exceed buying power, 1 order/60s rate limit

AlpacaHarness class with: health_check, fetch_bars, submit_order, get_position

## DELIVERABLE
File: mantis_core/physics/alpaca_harness.py

## CONSTRAINTS
- requests library for HTTP
- NEVER hardcode API keys
- Paper trading URL only
- Fail-closed on all exceptions
- Output valid Python only
