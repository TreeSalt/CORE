---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import dataclasses
from datetime import datetime, timezone
from typing import List, Dict, Any

@dataclasses.dataclass(frozen=True)
class DecayReport:
    timestamp: datetime
    decay_rate: float
    uncertainty: float
    source_counts: int
    status: str = "COMPLETED"

class AlphaDecayMonitor:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def record_paper_result(self, result_data: Dict[str, Any]) -> None:
        timestamp = result_data.get("timestamp", datetime.now(timezone.utc))
        rate = float(result_data.get("decay_rate", 0.0))
        confidence = result_data.get("confidence", 1.0)
        self._history.append({
            "source": "paper",
            "rate": rate,
            "timestamp": timestamp,
            "confidence": confidence
        })

    def record_live_result(self, result_data: Dict[str, Any]) -> None:
        timestamp = result_data.get("timestamp", datetime.now(timezone.utc))
        rate = float(result_data.get("decay_rate", 0.0))
        confidence = result_data.get("confidence", 1.0)
        self._history.append({
            "source": "live",
            "rate": rate,
            "timestamp": timestamp,
            "confidence": confidence
        })

    def compute_decay(self) -> DecayReport:
        if not self._history:
            return DecayReport(
                timestamp=datetime.now(timezone.utc),
                decay_rate=0.0,
                uncertainty=float('inf'),
                source_counts=0,
                status="NO_DATA"
            )

        rates = [r["rate"] * r.get("confidence", 1.0) for r in self._history]
        weights = [r.get("confidence", 1.0) for r in self._history]
        total_weight = sum(weights)

        if total_weight == 0:
            return DecayReport(
                timestamp=datetime.now(timezone.utc),
                decay_rate=0.0,
                uncertainty=float('inf'),
                source_counts=len(self._history),
                status="FAILED"
            )

        avg_rate = sum(rates) / total_weight
        
        if len(weights) > 1:
            weighted_mean_sq = sum(w * (r**2) for w, r in zip(weights, rates)) / total_weight
            weighted_sq_mean = sum(w * (avg_rate**2) for w, _ in zip(weights, rates)) / total_weight
            variance = weighted_mean_sq - avg_rate**2
            if variance < 0: variance = 0.0
            uncertainty = variance ** 0.5
        else:
            uncertainty = 0.0

        return DecayReport(
            timestamp=datetime.now(timezone.utc),
            decay_rate=avg_rate,
            uncertainty=uncertainty,
            source_counts=len(self._history),
            status="COMPLETED"
        )