# MISSION: Immutable Trade Ledger
DOMAIN: 05_REPORTING
TASK: implement_trade_ledger
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the paper trading system needs an append-only trade ledger
that records every fill, every P&L event, and every risk decision.
This is the evidentiary foundation for CP1 qualification.

## BLUEPRINT
Create a TradeLedger class that:
1. Stores trades in state/trade_ledger.jsonl (one JSON line per event)
2. Events: ENTRY, EXIT, STOP_HIT, DMS_TRIP, RISK_REJECT, DAY_END_FLATTEN
3. Each event has: timestamp, strategy_id, direction, price, quantity,
   pnl (for exits), cumulative_pnl, equity, drawdown_pct
4. The file is APPEND-ONLY — no deletions, no modifications
5. Each line includes a running SHA256 hash chain (hash of previous line)
6. Provides query methods: by_strategy, by_date_range, summary_stats
7. CP1 qualification check: count trades, compute Sharpe, compute max DD

## DELIVERABLE
File: 05_REPORTING/reporting_domain/trade_ledger.py

## CONSTRAINTS
- Append-only (constitutional requirement for CP1 evidence)
- Hash chain for tamper detection
- No external API calls
- Output valid Python only
