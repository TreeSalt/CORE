"""
antigravity_harness/capabilities.py
====================================
MISSION v4.5.340: Capability Inference Engine.

Generates CAPABILITY_SNAPSHOT.json from profile + config.
No secrets — all values from config/profile, not accounts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from mantis_core.utils import get_version_str

# ── Default Broker Capability Templates ────────────────────────────────────

BROKER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ibkr": {
        "role": "data_and_research",
        "account_type": "cash",
        "supports": {
            "equities": True,
            "fractional": True,
            "etfs": True,
            "options": False,
            "spreads": False,
            "crypto": False,
            "futures": True,
        },
    },
    "robinhood": {
        "role": "execution_stub",
        "account_type": "cash",
        "supports": {
            "equities": True,
            "fractional": True,
            "etfs": True,
            "options": True,
            "spreads": True,
            "crypto": True,
            "futures": False,
        },
    },
}


def generate_capability_snapshot(
    profile_path: str | Path,
    output_dir: str | Path,
    broker_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate CAPABILITY_SNAPSHOT.json from seed profile.

    Args:
        profile_path: Path to seed_profile.yaml.
        output_dir: Where to write CAPABILITY_SNAPSHOT.json.
        broker_overrides: Optional dict to override/add broker entries.

    Returns:
        The snapshot dict (also written to disk).
    """
    profile_path = Path(profile_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load profile
    profile: Dict[str, Any] = {}
    if profile_path.exists():
        with open(profile_path, encoding="utf-8") as f:
            profile = yaml.safe_load(f) or {}

    capital = profile.get("capital", {})
    starting_usd = capital.get("starting_usd", 0)
    instrument_universe = profile.get("instrument_universe", {})
    primary_instrument = instrument_universe.get("primary", "UNKNOWN")
    allowlist = instrument_universe.get("allowlist", [])
    execution = profile.get("execution", {})
    broker_cfg = execution.get("broker", {})
    primary_broker = broker_cfg.get("primary", "ibkr").lower()

    # Build broker capabilities
    brokers: Dict[str, Any] = {}
    for broker_name, template in BROKER_TEMPLATES.items():
        entry = {**template}
        entry["buying_power_cash_usd"] = starting_usd
        brokers[broker_name] = entry

    # Apply overrides
    if broker_overrides:
        for k, v in broker_overrides.items():
            if k in brokers:
                brokers[k].update(v)
            else:
                brokers[k] = v

    # MISSION v4.5.424: Identity Warden (SaaS Stub)
    operator_cfg = profile.get("operator", {})
    license_key = operator_cfg.get("license_key", "UNSET")
    license_status = "ACTIVE" if license_key == "DEV_SOVEREIGN_KEY_001" else "INVALID"

    snapshot: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "brokers": brokers,
        "profile_source": str(profile_path),
        "primary_broker": primary_broker,
        "primary_instrument": primary_instrument,
        "allowlist": allowlist,
        "buying_power_cash_usd": starting_usd,
        "license_key": license_key,
        "license_status": license_status,
        "trader_ops_version": get_version_str(),
        "TRADER_OPS_PROMPT_ID": os.environ.get("TRADER_OPS_PROMPT_ID", "UNSET"),
    }

    out_path = output_dir / "CAPABILITY_SNAPSHOT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)

    print(f"🔧 Capability Snapshot: {out_path.name} (${starting_usd} cash, broker={primary_broker})")
    return snapshot
