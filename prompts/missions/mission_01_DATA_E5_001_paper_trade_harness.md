# MISSION: Paper Trading Harness
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/paper_trade_harness.py

## REQUIREMENTS
- PaperTradeHarness class
- submit_order(symbol, side, qty, price) -> dict with order_id, status, fill_price
- get_position(symbol) -> dict with qty, avg_price, unrealized_pnl
- get_portfolio() -> dict with cash, positions, total_equity
- Simulates fills with configurable slippage (default 0.1%)
- Tracks all orders in an in-memory ledger
- No external calls of any kind
- Output valid Python only
