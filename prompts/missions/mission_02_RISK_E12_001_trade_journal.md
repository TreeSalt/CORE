# MISSION: Trade Journal — Paper Trading Logger
DOMAIN: 02_RISK_MANAGEMENT
TASK: 02_RISK_E12_001_trade_journal
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List
```

## CONTEXT
Every paper trade must be logged for post-mortem analysis. The journal stores
entries as JSON Lines (one JSON object per line) for efficient append-only writes
and streaming reads.

## REQUIREMENTS
Write `mantis_core/risk/trade_journal.py` containing:

- A dataclass `TradeEntry` with fields: trade_id (str), timestamp (str), symbol (str),
  side (str), size (float), price (float), regime (str), signal_type (str),
  stop_loss (Optional[float]), take_profit (Optional[float]), pnl (Optional[float]),
  closed (bool defaulting to False).
- A class `TradeJournal` initialized with a journal file path (default: state/trade_journal.jsonl).
  Methods:
  - `log_entry(entry)`: Append one TradeEntry as a JSON line to the file.
  - `close_trade(trade_id, exit_price)`: Find the entry by trade_id, compute PnL
    from entry price and exit price, mark it closed, rewrite the file.
  - `get_open_trades()`: Return a list of TradeEntry dicts where closed is False.
  - `export_csv(csv_path)`: Write all entries to a CSV file using csv.DictWriter.

## DELIVERABLE
File: mantis_core/risk/trade_journal.py

## CONSTRAINTS
- Append-only JSON Lines format for the journal
- Output valid Python only
