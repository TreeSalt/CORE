"""
fill_tape.py — Append-Only Fill Ledger + Slippage Drift Telemetry
=================================================================
Immutable record of all execution fills with real-time slippage
drift tracking. Designed for post-trade analysis and institutional
audit trails.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from antigravity_harness.execution.adapter_base import Fill, OrderSide


@dataclass
class SlippageDriftSnapshot:
    """Point-in-time slippage drift telemetry."""
    timestamp: datetime
    cumulative_slippage_bps: float
    rolling_mean_bps: float
    rolling_std_bps: float
    sample_count: int
    drift_alert: bool


class FillTape:
    """
    Append-Only Fill Ledger — Sovereign Execution Record.

    Features:
      - Immutable append-only fill storage
      - Real-time slippage drift monitoring
      - Per-symbol and aggregate telemetry
      - Drift alerting when slippage exceeds threshold

    The fill tape is the single source of truth for all executed trades.
    It cannot be modified after a fill is recorded (append-only).
    """

    def __init__(
        self,
        drift_alert_threshold_bps: float = 50.0,
        rolling_window: int = 20,
    ):
        self._fills: List[Fill] = []
        self._drift_alert_threshold = drift_alert_threshold_bps
        self._rolling_window = rolling_window
        self._snapshots: List[SlippageDriftSnapshot] = []

    @property
    def fills(self) -> List[Fill]:
        """Immutable view of all fills."""
        return list(self._fills)

    @property
    def fill_count(self) -> int:
        return len(self._fills)

    def record(self, fill: Fill) -> Optional[SlippageDriftSnapshot]:
        """
        Record a fill to the tape. Returns a drift snapshot if
        the slippage drift exceeds the alert threshold.

        This is the ONLY way to add fills — no mutation, no deletion.
        """
        self._fills.append(fill)
        snapshot = self._compute_drift_snapshot(fill.timestamp)
        self._snapshots.append(snapshot)

        if snapshot.drift_alert:
            return snapshot
        return None

    def _compute_drift_snapshot(self, timestamp: datetime) -> SlippageDriftSnapshot:
        """Compute current slippage drift telemetry."""
        all_slippage = [f.slippage_bps for f in self._fills]
        cumulative = sum(all_slippage)

        # Rolling window
        window = all_slippage[-self._rolling_window:]
        rolling_mean = statistics.mean(window) if window else 0.0
        rolling_std = statistics.stdev(window) if len(window) >= 2 else 0.0

        drift_alert = abs(rolling_mean) > self._drift_alert_threshold

        return SlippageDriftSnapshot(
            timestamp=timestamp,
            cumulative_slippage_bps=round(cumulative, 4),
            rolling_mean_bps=round(rolling_mean, 4),
            rolling_std_bps=round(rolling_std, 4),
            sample_count=len(self._fills),
            drift_alert=drift_alert,
        )

    def get_fills_by_symbol(self, symbol: str) -> List[Fill]:
        """Get all fills for a specific symbol."""
        return [f for f in self._fills if f.symbol == symbol]

    def get_fills_by_side(self, side: OrderSide) -> List[Fill]:
        """Get all fills for a specific side."""
        return [f for f in self._fills if f.side == side]

    def get_telemetry(self) -> Dict[str, Any]:
        """Return aggregate telemetry summary."""
        if not self._fills:
            return {
                "total_fills": 0,
                "total_slippage_bps": 0.0,
                "avg_slippage_bps": 0.0,
                "max_slippage_bps": 0.0,
                "min_slippage_bps": 0.0,
                "drift_alerts": 0,
                "symbols": [],
            }

        all_slippage = [f.slippage_bps for f in self._fills]
        symbols = list({f.symbol for f in self._fills})

        return {
            "total_fills": len(self._fills),
            "total_slippage_bps": round(sum(all_slippage), 4),
            "avg_slippage_bps": round(statistics.mean(all_slippage), 4),
            "max_slippage_bps": round(max(all_slippage), 4),
            "min_slippage_bps": round(min(all_slippage), 4),
            "drift_alerts": sum(1 for s in self._snapshots if s.drift_alert),
            "symbols": symbols,
        }

    def get_per_symbol_telemetry(self) -> Dict[str, Dict[str, Any]]:
        """Return per-symbol slippage breakdown."""
        result: Dict[str, Dict[str, Any]] = {}
        symbols = {f.symbol for f in self._fills}

        for sym in symbols:
            sym_fills = self.get_fills_by_symbol(sym)
            slippages = [f.slippage_bps for f in sym_fills]
            result[sym] = {
                "fill_count": len(sym_fills),
                "avg_slippage_bps": round(statistics.mean(slippages), 4),
                "total_slippage_bps": round(sum(slippages), 4),
                "total_qty": round(sum(f.qty for f in sym_fills), 6),
                "total_commission": round(sum(f.commission for f in sym_fills), 4),
            }

        return result
