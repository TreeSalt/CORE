---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass(frozen=True)
class DecayReport:
    original_value: float
    current_value: float
    decay_rate: float
    timestamp: datetime

class AlphaDecayMonitor:
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record_paper_result(self, value: float, metadata: Dict[str, Any]) -> None:
        self._records.append({
            "source": "paper",
            "value": value,
            "metadata": metadata,
            "timestamp": datetime.now()
        })

    def record_live_result(self, value: float, metadata: Dict[str, Any]) -> None:
        self._records.append({
            "source": "live",
            "value": value,
            "metadata": metadata,
            "timestamp": datetime.now()
        })

    def compute_decay(self) -> DecayReport:
        if not self._records:
            return DecayReport(0.0, 0.0, 0.0, datetime.now())

        sorted_records = sorted(self._records, key=lambda r: r["timestamp"])
        oldest = sorted_records[0]
        newest = sorted_records[-1]

        orig = oldest["value"]
        curr = newest["value"]

        decay_rate = (orig - curr) / abs(orig) if orig != 0 else 0.0

        return DecayReport(
            original_value=orig,
            current_value=curr,
            decay_rate=decay_rate,
            timestamp=datetime.now()
        )<|endoftext|><|im_start|>user