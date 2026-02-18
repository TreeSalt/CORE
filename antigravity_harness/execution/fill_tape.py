"""
antigravity_harness/execution/fill_tape.py
==========================================
FillTape — deterministic record of every execution.

Records fills with slippage_realized_ticks for every trade.
Compares realized slippage against the buffer (4 ticks from seed_profile).
Emits a profile flag artifact (does NOT auto-edit profile) if drift detected.

Drift trigger: if realized slippage > buffer in > 20% of fills in a run,
write a ProfileDriftFlag to evidence for operator review.

Does NOT: modify seed_profile. Does NOT make trading decisions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from antigravity_harness.execution.adapter_base import Fill, OrderSide
from antigravity_harness.instruments.mes import (
    MES_SLIPPAGE_BUFFER_TICKS,
    MES_TICK_SIZE,
    MES_TICK_VALUE,
)

logger = logging.getLogger("FILL_TAPE")

DRIFT_THRESHOLD_PCT: float = 0.20  # 20% of fills exceeding buffer triggers drift flag


# ─── Enriched Fill Record ─────────────────────────────────────────────────────


@dataclass
class FillRecord:
    """
    A fill with slippage analysis attached.
    Written to the FillTape CSV and used for post-session analysis.
    """
    # Identity
    broker_order_id: str
    client_order_id: str
    symbol: str
    side: str                           # "BUY" or "SELL"
    filled_qty: int
    fill_price: float
    fill_time_utc: str                  # ISO format

    # Slippage analysis (Forensic Drift)
    expected_price: Optional[float]     # Mid price at order submission time
    actual_price: float                 # fill_price (for explicit comparison)
    drift_pts: Optional[float]          # Actual - Expected (signed)
    drift_bps: Optional[float]          # Drift as Basis Points of Expected
    slippage_realized_ticks: Optional[int]
    slippage_buffer_ticks: int          # From seed profile (4)
    slippage_exceeded_buffer: bool

    # Cost
    commission_usd: float
    slippage_cost_usd: float            # slippage_realized_ticks * tick_value

    # Session context
    session_trade_number: int           # 1st, 2nd, 3rd trade today


# ─── FillTape ─────────────────────────────────────────────────────────────────


class FillTape:
    """
    Append-only log of all fills for a trading session.

    Usage:
        tape = FillTape(output_dir=Path("reports/fills"), session_date="2026-02-17")
        tape.record(fill, expected_price=mid_at_submission)
        tape.close()   # writes CSV + manifest entry

    The tape file is deterministic: same fills produce same bytes.
    SHA256 of the tape is recorded in EVIDENCE_MANIFEST.json.
    """

    def __init__(
        self,
        output_dir: Path,
        session_date: str,
        slippage_buffer_ticks: int = MES_SLIPPAGE_BUFFER_TICKS,
    ) -> None:
        self.output_dir = output_dir
        self.session_date = session_date
        self.slippage_buffer_ticks = slippage_buffer_ticks
        self._records: List[FillRecord] = []
        self._trade_count = 0

        output_dir.mkdir(parents=True, exist_ok=True)
        self._tape_path = output_dir / "fill_tape.csv"

    def record(
        self,
        fill: Fill,
        expected_price: Optional[float] = None,
    ) -> FillRecord:
        """
        Record a fill with slippage analysis.

        Args:
            fill: The confirmed fill from the broker.
            expected_price: The mid price when the order was submitted.
                            Used to compute realized slippage.
                            Pass None if unknown (slippage_realized_ticks will be None).
        """
        self._trade_count += 1

        # Compute realized slippage and drift
        slippage_ticks: Optional[int] = None
        slippage_cost_usd: float = 0.0
        drift_pts: Optional[float] = None
        drift_bps: Optional[float] = None

        if expected_price is not None:
            fill_px = float(fill.fill_price)
            # Drift is (Actual - Expected). Positive drift on BUY is BAD.
            drift_pts = fill_px - expected_price if fill.side == OrderSide.BUY else expected_price - fill_px
            drift_bps = (drift_pts / expected_price) * 10000 if expected_price > 0 else 0.0
            
            # Slippage in ticks
            slippage_ticks = round(drift_pts / MES_TICK_SIZE) if drift_pts is not None else None
            slippage_cost_usd = max(0, slippage_ticks or 0) * MES_TICK_VALUE * fill.filled_qty

        exceeded = (
            slippage_ticks is not None
            and slippage_ticks > self.slippage_buffer_ticks
        )

        record = FillRecord(
            broker_order_id=fill.broker_order_id,
            client_order_id=fill.client_order_id,
            symbol=fill.symbol,
            side=fill.side.value,
            filled_qty=fill.filled_qty,
            fill_price=float(fill.fill_price),
            fill_time_utc=fill.fill_time_utc.isoformat(),
            expected_price=expected_price,
            actual_price=float(fill.fill_price),
            drift_pts=drift_pts,
            drift_bps=drift_bps,
            slippage_realized_ticks=slippage_ticks,
            slippage_buffer_ticks=self.slippage_buffer_ticks,
            slippage_exceeded_buffer=exceeded,
            commission_usd=fill.commission_usd,
            slippage_cost_usd=slippage_cost_usd,
            session_trade_number=self._trade_count,
        )

        self._records.append(record)

        # Attach slippage back to the fill object for safety layer
        fill.slippage_realized_ticks = slippage_ticks

        logger.info(
            f"FillTape #{self._trade_count}: {fill.symbol} {fill.side.value} "
            f"@{float(fill.fill_price):.2f} slippage={slippage_ticks}tks "
            f"{'⚠️ EXCEEDED BUFFER' if exceeded else '✅'}"
        )

        return record

    def close(self) -> Path:
        """
        Write CSV tape and check for slippage drift.
        Returns path to the written tape file.
        """
        if not self._records:
            logger.info("FillTape: no fills this session.")
            return self._tape_path

        # Write deterministic CSV (fixed column order)
        fieldnames = list(FillRecord.__dataclass_fields__.keys())
        with open(self._tape_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self._records:
                writer.writerow(asdict(r))

        # Check for drift
        self._check_slippage_drift()

        tape_hash = hashlib.sha256(self._tape_path.read_bytes()).hexdigest()
        logger.info(f"FillTape closed: {self._tape_path} sha256={tape_hash[:16]}…")
        return self._tape_path

    def _check_slippage_drift(self) -> None:
        """
        If realized slippage exceeds buffer in > 20% of fills:
        emit ProfileDriftFlag artifact for operator review.

        Does NOT modify seed_profile. Does NOT pause trading.
        """
        fills_with_known_slippage = [
            r for r in self._records if r.slippage_realized_ticks is not None
        ]
        if not fills_with_known_slippage:
            return

        exceeded_count = sum(1 for r in fills_with_known_slippage if r.slippage_exceeded_buffer)
        drift_pct = exceeded_count / len(fills_with_known_slippage)

        if drift_pct > DRIFT_THRESHOLD_PCT:
            self._emit_drift_flag(drift_pct, exceeded_count, len(fills_with_known_slippage))

    def _emit_drift_flag(
        self,
        drift_pct: float,
        exceeded_count: int,
        total_count: int,
    ) -> None:
        """
        Write a ProfileDriftFlag JSON artifact. Operator must review and
        explicitly update the slippage buffer in seed_profile if warranted.
        """
        flag = {
            "flag_type": "SLIPPAGE_DRIFT",
            "session_date": self.session_date,
            "drift_pct": round(drift_pct, 4),
            "fills_exceeding_buffer": exceeded_count,
            "fills_with_known_slippage": total_count,
            "drift_threshold_pct": DRIFT_THRESHOLD_PCT,
            "slippage_buffer_ticks_current": self.slippage_buffer_ticks,
            "action_required": (
                "Realized slippage exceeded the profile buffer in "
                f"{drift_pct:.1%} of fills. Review fill_tape CSV and consider "
                "updating seed_profile slippage_buffer_ticks. "
                "DO NOT auto-update — operator must confirm."
            ),
        }
        flag_path = self.output_dir / f"profile_drift_flag_{self.session_date}.json"
        flag_path.write_text(json.dumps(flag, indent=2))
        logger.warning(
            f"⚠️ SLIPPAGE DRIFT FLAG emitted: {drift_pct:.1%} of fills exceeded "
            f"{self.slippage_buffer_ticks}-tick buffer. See {flag_path}"
        )

    @property
    def records(self) -> List[FillRecord]:
        """Read-only access to all recorded fills this session."""
        return list(self._records)

    def summary(self) -> dict:
        """Return a summary dict for evidence manifest."""
        filled = [r for r in self._records if r.slippage_realized_ticks is not None]
        mean_slip = (
            sum(r.slippage_realized_ticks for r in filled) / len(filled)
            if filled else None
        )
        return {
            "session_date": self.session_date,
            "total_fills": len(self._records),
            "fills_with_slippage_data": len(filled),
            "mean_slippage_ticks": round(mean_slip, 2) if mean_slip is not None else None,
            "fills_exceeding_buffer": sum(1 for r in filled if r.slippage_exceeded_buffer),
            "drift_threshold_pct": DRIFT_THRESHOLD_PCT,
        }
