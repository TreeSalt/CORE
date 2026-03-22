import json
import os
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from mantis_core.paths import STATE_DIR

REGISTRY_PATH = STATE_DIR / "champion_registry.json"


def load_registry() -> Dict[str, Any]:
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}


def save_registry(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True, default=str)


def check_drift(candidate: Dict[str, Any], anchor: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if candidate has drifted significantly from anchor.
    Returns (is_drifted, reason).
    Drift if:
    - PF drops > 20%
    - MaxDD increases > 20%
    """
    # PF
    c_pf = float(candidate.get("profit_factor", 0.0))
    a_pf = float(anchor.get("profit_factor", 0.0))
    if a_pf > 0 and c_pf < (a_pf * 0.80):
        return True, f"PF Drift: {c_pf:.2f} < 0.8*{a_pf:.2f}"

    # MaxDD
    c_dd = float(candidate.get("max_dd_pct", 0.0))
    a_dd = float(anchor.get("max_dd_pct", 0.0))
    # DD is typically positive float (0.15).
    c_dd = abs(c_dd)
    a_dd = abs(a_dd)

    # If anchor DD is tiny (e.g. 0.01), 20% increase is noise.
    if a_dd > 0 and c_dd > (a_dd * 1.20):
        return True, f"MaxDD Drift: {c_dd:.1%} > 1.2*{a_dd:.1%}"

    return False, "Stable"


def promote_to_staging(
    symbol: str,
    timeframe: str,
    candidate: Dict[str, Any],
    anchor_metrics: Optional[Dict[str, Any]] = None,
    reset_anchor: bool = False,
) -> Dict[str, Any]:
    """
    Promote a candidate to STAGING in the registry.
    If reset_anchor is True, overwrites the anchor metrics.
    Otherwise, preserves existing anchor (Anti-Drift Gaming).
    """
    reg = load_registry()
    key = f"{symbol}_{timeframe}"

    current_entry = reg.get(key, {})
    existing_anchor = current_entry.get("anchor_metrics")

    # Anchor Selection Logic
    final_anchor = None

    final_anchor = (anchor_metrics or candidate) if reset_anchor else (existing_anchor or (anchor_metrics or candidate))

    # Drift Check (against the Final Anchor we decided on)
    drift, reason = check_drift(candidate, final_anchor)
    # If we are resetting, drift check might be moot (comparing to self), but safe to run.
    # If preserving, we compare new candidate to OLD anchor.
    if drift and not reset_anchor:
        # If resetting, we accept the new reality (re-baselining).
        # If NOT resetting, drift is a blocker.
        return {"status": "FAIL", "reason": f"Anchor Drift: {reason}"}

    # Update Registry
    entry = {
        "status": "PASS",  # Validation Status
        "deployment_state": "STAGING",  # Phase 6F Restriction: No Auto-LIVE
        "updated_at": str(pd.Timestamp.now()),
        "metrics": candidate,
        "anchor_metrics": final_anchor,
    }

    reg[key] = entry
    save_registry(reg)

    return {"status": "PASS", "message": f"Promoted {key} to STAGING", "anchor_reset": reset_anchor}
