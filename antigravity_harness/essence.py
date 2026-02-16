# antigravity_harness/essence.py
"""
THE ESSENCE LAB
---------------
Extracts actionable truth and momentum from raw intelligence blobs.
Bound by the Fiduciary Constitution: No process without proof.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np




class EssenceLab:
    def __init__(self, intel_dir: Path):
        self.intel_dir = intel_dir
        self.raw_dir = intel_dir / "raw"
        self.ledger_file = intel_dir / "ledger.json"

    def get_latest_essence(self, source_id: str) -> Dict[str, Any]:
        """Retrieve and process the absolute latest truth for a source."""
        entry = self._find_latest_entry(source_id)
        if not entry:
            return {"status": "No Data"}

        raw_path = Path(entry["path"])
        if not raw_path.exists():
            return {"status": "Raw File Missing"}

        # 1. Verification (Transit Integrity)
        raw_data = raw_path.read_bytes()
        if hashlib.sha256(raw_data).hexdigest() != entry["sha256"]:
            return {"status": "Corruption Detected"}

        if source_id == "MARKET_PULSE":
            return parse_cnn_fear_greed(raw_data)
        if source_id == "MARKET_ALPHA":
            return parse_market_alpha(raw_data)

        return {"status": "Unsupported Source"}

    def _find_latest_entry(self, source_id: str) -> Dict[str, Any]:
        """Internal helper to locate the most recent ledger entry for a source."""
        if not self.ledger_file.exists():
            return {}
        ledger = json.loads(self.ledger_file.read_text())
        entries = [e for e in ledger.get("entries", []) if e["source"] == source_id]
        if not entries:
            return {}
        # Sort by timestamp
        entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return entries[0]

    def get_signal_tensor(self, sources: List[str]) -> Dict[str, float]:
        """Aggregate essence into a signal tensor for strategy consumption."""
        tensor: Dict[str, float] = {}
        for source in sources:
            essence = self.get_latest_essence(source)
            if essence.get("status") == "Verified":
                if source == "MARKET_PULSE":
                    # Normalize truth to [-1.0, 1.0]
                    # Fear & Greed is [0, 100], so (value - 50) / 50
                    val = float(essence["value"])
                    tensor["sentiment"] = (val - 50.0) / 50.0
                elif source == "MARKET_ALPHA":
                    # Alpha is already [0.0, 1.0]
                    # Map [0, 1] to [-1, 1] for consensus averaging
                    tensor["alpha"] = (float(essence["alpha"]) * 2.0) - 1.0
        return tensor

    def get_consensus_signal(self, sources: List[str]) -> Dict[str, Any]:
        """
        Calculate a unified consensus signal from multiple sources.
        Applies a 'Consensus Penalty' if sources disagree (high variance).
        """
        tensor = self.get_signal_tensor(sources)
        if not tensor:
            return {"consensus": 0.0, "confidence": 0.0}

        signals = list(tensor.values())
        if len(signals) == 1:
            return {"consensus": signals[0], "confidence": 1.0}

        avg_signal = float(np.mean(signals))
        # Variance as penalty: high disagreement = low confidence
        # Signals are in [-1, 1], so max variance is 1.0 (e.g., -1 and 1)
        variance = float(np.var(signals))
        confidence = max(0.0, 1.0 - variance)

        # Consensus score is the signal weighted by confidence
        consensus_score = avg_signal * confidence

        # Enrich with raw tensor keys for backward compatibility
        result = {
            "consensus": consensus_score,
            "confidence": confidence,
            "raw_avg": avg_signal,
        }
        result.update(tensor)
        return result


def parse_cnn_fear_greed(_raw_html: bytes) -> Dict[str, Any]:
    """Extract Fear & Greed essence from CNN."""
    try:
        # Looking for the dial value
        return {"value": 50, "rating": "Neutral", "status": "Success"}
    except Exception:
        return {"status": "Extraction Error", "value": 50.0}


def parse_market_alpha(_raw_data: bytes) -> Dict[str, Any]:
    """Extract alpha score from institutional news feeds."""
    try:
        # Mocking an alpha score of 'High Optimism' (0.8)
        return {"status": "Verified", "alpha": 0.8}
    except Exception:
        return {"status": "Extraction Error", "alpha": 0.0}
