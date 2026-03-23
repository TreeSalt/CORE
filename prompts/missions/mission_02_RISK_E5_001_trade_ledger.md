# MISSION: Append-Only Trade Ledger
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/trade_ledger.py

## REQUIREMENTS
- SQLite database, append-only (no UPDATE/DELETE)
- Schema: id, timestamp, strategy_id, symbol, side, qty, price, pnl, prev_hash, entry_hash
- entry_hash = sha256(prev_hash + timestamp + strategy_id + side + qty + price)
- record_trade() -> entry; verify_chain() -> bool; get_trades() -> list
- No method to delete or modify records
- No external API calls
- Output valid Python only
