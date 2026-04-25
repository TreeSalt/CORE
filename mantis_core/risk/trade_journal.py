import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class TradeEntry:
    trade_id: str
    timestamp: str
    symbol: str
    side: str
    size: float
    price: float
    regime: str
    signal_type: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl: Optional[float]
    closed: bool = False

class TradeJournal:
    def __init__(self, journal_file_path: Optional[str] = "state/trade_journal.jsonl"):
        self.journal_path = Path(journal_file_path) if isinstance(journal_file_path, str) else journal_path

    def log_entry(self, entry):
        # Ensure directory exists for the file path before writing
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.journal_path, 'a', encoding='utf-8') as f:
            json.dump(asdict(entry), f)
            f.write('\n')

    def close_trade(self, trade_id, exit_price):
        entries = []
        if self.journal_path.exists():
            with open(self.journal_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        
        trade_found = False
        
        # Iterate and update PnL for the matching entry
        for i, entry in enumerate(entries):
            if entry.get('trade_id') == trade_id and not entry.get('closed'):
                side = entry['side'].lower()
                current_price = float(entry['price'])
                exit_val = float(exit_price)
                
                # Calculate PnL based on side (Buy/Long vs Sell/Short)
                if side in ['buy', 'long']:
                    pnl = (exit_val - current_price) * entry['size']
                elif side in ['sell', 'short']:
                    pnl = (current_price - exit_val) * entry['size']
                
                entries[i]['closed'] = True
                entries[i]['pnl'] = pnl
                trade_found = True
        
        # Only rewrite if we found the trade (optional, but cleaner to update PnL)
        # The prompt implies just updating or writing nothing. 
        # However, appending logic: If trade not found, we should ideally NOT change file? 
        # Or just leave it. But to be safe on state consistency (pnl calc requires data),
        # if not found, no op is needed or just update PnL. 
        # I'll check if any changes were made to avoid unnecessary reads/writes.
        
        if trade_found:
            with open(self.journal_path, 'w', encoding='utf-8') as f:
                for e in entries:
                    json.dump(e, f)
                    f.write('\n')

    def get_open_trades(self):
        entries = []
        if self.journal_path.exists():
            with open(self.journal_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if not data.get('closed'):
                                entries.append(data)
                        except json.JSONDecodeError:
                            pass
        return entries

    def export_csv(self, csv_path):
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        
        all_entries = []
        with open(self.journal_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        all_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as out_f:
            fieldnames = list(TradeEntry.__dataclass_fields__.keys())
            writer = csv.DictWriter(out_f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in all_entries:
                # Convert float fields to avoid scientific notation if strictly needed, 
                # but standard csv writer works fine.
                writer.writerow(entry)
