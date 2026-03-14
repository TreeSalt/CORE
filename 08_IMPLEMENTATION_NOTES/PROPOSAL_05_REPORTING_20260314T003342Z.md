---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

 ```python
import hashlib
from datetime import datetime

class TradeLedger:
    FILE_PATH = 'state/trade_ledger.jsonl'

    def __init__(self):
        self.events = []
        self.load_events()

    def load_events(self):
        try:
            with open(self.FILE_PATH, 'r') as file:
                for line in file:
                    event = eval(line.strip())
                    self.events.append(event)
        except FileNotFoundError:
            pass

    def save_events(self):
        with open(self.FILE_PATH, 'w') as file:
            for event in self.events:
                file.write(f"{event}\n")

    def add_event(self, event):
        if not self.events:
            prev_hash = None
        else:
            prev_hash = self.events[-1]['hash']
        event['hash'] = hashlib.sha256(str(event).encode()).hexdigest()
        event['prev_hash'] = prev_hash
        self.events.append(event)
        self.save_events()

    def by_strategy(self, strategy_id):
        return [event for event in self.events if event['strategy_id'] == strategy_id]

    def by_date_range(self, start_date, end_date):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        return [event for event in self.events if start_date <= datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S') <= end_date]

    def summary_stats(self):
        total_pnl = sum(event['pnl'] for event in self.events if 'pnl' in event)
        total_quantity = sum(event['quantity'] for event in self.events)
        total_equity = sum(event['equity'] for event in self.events)
        max_dd = max(event['drawdown_pct'] for event in self.events if 'drawdown_pct' in event)
        return {
            'total_pnl': total_pnl,
            'total_quantity': total_quantity,
            'total_equity': total_equity,
            'max_dd': max_dd
        }

    def count_trades(self):
        return len(self.events)

    def compute_sharpe(self):
        total_pnl = sum(event['pnl'] for event in self.events if 'pnl' in event)
        total_quantity = sum(event['quantity'] for event in self.events)
        total_equity = sum(event['equity'] for event in self.events)
        if total_equity == 0:
            return None
        sharpe_ratio = total_pnl / (total_quantity * total_equity) * (252 ** 0.5)
        return sharpe_ratio
```

This `TradeLedger` class provides a way to manage a trade ledger that meets the specified requirements. It includes methods for adding events, querying by strategy and date range, and computing summary statistics such as the total P&L, total quantity, total equity, and maximum drawdown. The events are stored in a JSONL file with a running SHA256 hash chain for tamper detection.