import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class StrategyLedger:
    """
    Item 24: Immutable Strategy Ledger.
    Backward-hashed audit trail of all verified strategy deployments.
    """
    def __init__(self, ledger_path: Path):
        self.path = ledger_path

    def load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with open(self.path, "r") as f:
            return json.load(f)

    def append(self, strategy_id: str, commitment: Dict[str, str], audit_report_path: str):
        ledger = self.load()
        prev_hash = ledger[-1]["commitment"]["commitment_hash"] if ledger else "GENESIS"
        
        entry = {
            "timestamp": datetime.now().timestamp(),
            "timestamp_utc": datetime.utcnow().isoformat(),
            "strategy_id": strategy_id,
            "commitment": commitment,
            "audit_report_ref": str(audit_report_path),
            "prev_hash": prev_hash
        }
        
        ledger.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(ledger, f, indent=2)
        return entry
