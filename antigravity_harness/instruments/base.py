from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentSpec:
    """
    CANONICAL INSTRUMENT PHYSICS — TRADER_OPS v4.5.382
    Defines the immutable laws of trading for a specific instrument.
    This spec is hashed and bound to execution artifacts to prevent
    semantic corruption (Frankenstein Fills).
    """
    symbol: str
    asset_class: str
    tick_size: float
    multiplier: float
    lot_size: float = 1.0

    @property
    def sha256(self) -> str:
        """Deterministic fingerprint of instrument physics."""
        data = {
            "symbol": self.symbol,
            "asset_class": self.asset_class,
            "tick_size": float(self.tick_size),
            "multiplier": float(self.multiplier),
            "lot_size": float(self.lot_size),
        }
        # Sorted keys for idempotency
        payload = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

# ─── Standard Test Spec ──────────────────────────────────────────────────────
TEST_SPEC = InstrumentSpec(
    symbol="GENERIC",
    asset_class="test",
    tick_size=0.01,
    multiplier=1.0,
    lot_size=1.0
)
