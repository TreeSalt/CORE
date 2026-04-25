---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
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

```<|endoftext|><|im_start|>user
Wait, you Wait, one detail about `close_trade`: if trade_id not found? I'll just do nothing or update if found. The prompt says "Close a trade" implies it exists.
    
    Double check `log_entry` arguments: entry (TradeEntry instance). `asdict` handles this.
    
    One edge case in `close_trade`: what if the journal file is empty or doesn't exist? `entries` starts as `[]`, loop finds nothing, writes nothing (overwrites with empty file). This is acceptable behavior or error. I'll stick to basic logic.

    Wait, the prompt implies `state/trade_journal.jsonl` default path. I should use `self.journal_path`.
    
    One tiny detail: "No markdown". Just the python code.
    
    Let's finalize imports. `from typing import Optional, List`. `List` is not used in signature but good to have if needed? Not needed strictly but standard. The prompt doesn't forbid unused imports. I will remove unused to be clean. `List` isn't used in methods signature or body (only inferred).
    Actually, `get_open_trades` returns list, `export_csv` reads lines.
    
    Let's write it out clearly.

    One potential issue: `csv.DictWriter` with fields from dataclass. If JSON stores floats without precision loss issues? Standard `json.dump` handles floats.

    Wait, the prompt asks for "default: state/trade_journal.jsonl". This is a relative path. The code should handle that.
    
    Also `Path('state/trade_journal.jsonl')` creates path.
    
    Re-check `export_csv`: `csv_path`. It should be a string or Path. I'll ensure it creates parent dir if needed? `Path(csv_path).parent.mkdir(...)`

    Okay, ready to generate.
    
    Wait, looking at `log_entry` again. The requirement says: "The default path is state/trade_journal.jsonl". And `__init__` takes `journal_file_path`.
    
    One small nuance: `stop_loss` and `take_profit` are optional. If they are not passed to `__init__`, they might be None. The JSON dump handles `None`.

    One more thing: `from datetime import datetime, timezone`. In the code I didn't actually use these yet in the snippet I mentally wrote because the method just takes entry (which has timestamp). I should keep them for robustness? The class `TradeEntry` requires string timestamp. If user passes a Timestamp object to constructor? The prompt says "timestamp: str". So user must provide formatted string. But usually one formats it using `datetime`. I will leave the import there as requested or strictly needed? The code snippet in my mind doesn't convert, but having imports is safer if used elsewhere. I'll keep imports minimal and relevant. The `log_entry` accepts an entry (TradeEntry instance), which implies the user creates the object first. I won't add a helper method to create it unless asked.
    
    Actually, looking at imports requested: "import json", "import csv", "from datetime import datetime, timezone", "from pathlib import Path", "from dataclasses import dataclass, asdict", "from typing import Optional, List". All requested explicitly. I should include all of them to satisfy the prompt's implied requirement list if it was explicit. The user said "You must use these specific imports". It wasn't strictly listed but the system prompt says so in a hidden thought.
    
    Okay, final check: ensure code is clean and follows best practices.
</think>

```python
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
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: Optional[float] = None
    closed: bool = False

class TradeJournal:
    def __init__(self, journal_file_path: Optional[str] = "state/trade_journal.jsonl"):
        self.journal_path = Path(journal_file_path) if isinstance(journal_file_path, str) else journal_path

    def log_entry(self, entry):
        # Ensure directory exists before writing
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.journal_path, 'a', encoding='utf-8') as f:
            json.dump(asdict(entry), f)
            f.write('\n')

    def close_trade(self, trade_id, exit_price):
        entries = []
        # Read all lines into a list if file exists and is not empty
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
        
        # Write back only if changes were made or to preserve updated state? 
        # Prompt doesn't specify but standard is to write. If no match, file unchanged.
        # I'll write regardless to ensure consistency if matches found.
        # If no matches (trade not found), do nothing (file remains same).
        # To be safe: if trade_found, rewrite; else don't touch file. 
        # Writing empty list would overwrite data. So conditional write is safer.
        
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
                writer.writerow(entry)
```