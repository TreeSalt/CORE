"""
antigravity_harness/tradability.py
===================================
MISSION v4.5.340: Instrument Viability Engine.

Evaluates whether each candidate instrument is tradable given the
current capability snapshot (broker, capital, permissions).
Selects the first viable asset class for smoke testing.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from antigravity_harness.utils import get_version_str

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Reason Codes ──────────────────────────────────────────────────────────

VIABLE = "VIABLE"
INSUFFICIENT_CAPITAL_MIN_UNIT = "INSUFFICIENT_CAPITAL_MIN_UNIT"
PERMISSION_DENIED = "PERMISSION_DENIED"
PROFILE_DENYLIST = "PROFILE_DENYLIST"
DATA_MISSING = "DATA_MISSING"
MARKET_CLOSED = "MARKET_CLOSED"
CANNOT_SHORT_CASH_ACCOUNT = "CANNOT_SHORT_CASH_ACCOUNT"
LICENSE_INVALID = "LICENSE_INVALID"


# ── Default Candidate Instruments ─────────────────────────────────────────

DEFAULT_CANDIDATES: List[Dict[str, Any]] = [
    # ETFs (priority 1)
    {"symbol": "SPY", "asset_class": "etf", "min_unit": 1, "min_cost_usd": 600.0, "fractional": True},
    {"symbol": "QQQ", "asset_class": "etf", "min_unit": 1, "min_cost_usd": 500.0, "fractional": True},
    {"symbol": "IWM", "asset_class": "etf", "min_unit": 1, "min_cost_usd": 220.0, "fractional": True},
    # Equities (priority 2)
    {"symbol": "AAPL", "asset_class": "equity", "min_unit": 1, "min_cost_usd": 250.0, "fractional": True},
    {"symbol": "MSFT", "asset_class": "equity", "min_unit": 1, "min_cost_usd": 450.0, "fractional": True},
    {"symbol": "NVDA", "asset_class": "equity", "min_unit": 1, "min_cost_usd": 140.0, "fractional": True},
    # Crypto (priority 3)
    {"symbol": "BTC", "asset_class": "crypto", "min_unit": 0.0001, "min_cost_usd": 10.0, "fractional": True},
    {"symbol": "ETH", "asset_class": "crypto", "min_unit": 0.001, "min_cost_usd": 3.0, "fractional": True},
    # Futures (expected blocked on small cash accounts)
    {"symbol": "MES", "asset_class": "future", "min_unit": 1, "min_cost_usd": 26500.0, "fractional": False},
]

# Priority order for smoke universe selection
ASSET_CLASS_PRIORITY = ["future", "etf", "equity", "crypto"]


def get_allowlist_override(config_dir: Path) -> Tuple[List[str], str]:
    """MISSION v4.5.382: Allowlist Override Binding."""
    override_path = config_dir / "ALLOWLIST_OVERRIDE.json"
    if override_path.exists():
        try:
            with open(override_path, "r") as f:
                data = json.load(f)
                symbols = data.get("allowlist", [])
                h = hashlib.sha256(override_path.read_bytes()).hexdigest()
                return symbols, h
        except Exception:
            pass
    return [], "N/A"


def _check_license(capabilities: Dict[str, Any]) -> Tuple[bool, str]:
    """MISSION v4.5.424: Identity Warden (SaaS Stub)."""
    status = capabilities.get("license_status", "INVALID")
    if status == "ACTIVE":
        return True, "ACTIVE"
    return False, LICENSE_INVALID


def _check_viability(
    instrument: Dict[str, Any],
    capabilities: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Evaluate a single instrument against capabilities.

    Returns:
        (viable: bool, reason: str)
    """
    symbol = instrument["symbol"]
    asset_class = instrument["asset_class"]
    min_cost = instrument["min_cost_usd"]
    fractional = instrument["fractional"]

    buying_power = capabilities.get("buying_power_cash_usd", 0)
    brokers = capabilities.get("brokers", {})
    primary_broker = capabilities.get("primary_broker", "ibkr")
    broker_caps = brokers.get(primary_broker, {})
    supports = broker_caps.get("supports", {})

    # 1. Permission check — does the broker support this asset class?
    asset_class_map = {
        "etf": "etfs",
        "equity": "equities",
        "crypto": "crypto",
        "future": "futures",
    }
    support_key = asset_class_map.get(asset_class, asset_class)
    if not supports.get(support_key, False):
        return False, PERMISSION_DENIED

    # 2. Allowlist check — strict DEFAULT-DENY
    # MISSION v4.5.382: Support override binding
    allowlist = capabilities.get("allowlist", [])
    if allowlist and symbol not in allowlist:
        return False, PROFILE_DENYLIST

    # 3. Capital check — can we afford the minimum unit?
    if not fractional and buying_power < min_cost:
        return False, INSUFFICIENT_CAPITAL_MIN_UNIT

    # For fractional instruments, even $1 is enough (broker supports fractional)
    if fractional and not supports.get("fractional", False) and buying_power < min_cost:
        return False, INSUFFICIENT_CAPITAL_MIN_UNIT

    return True, VIABLE


def generate_viability_table(
    capabilities: Dict[str, Any],
    output_dir: str | Path,
    candidates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generate INSTRUMENT_VIABILITY_TABLE.json.

    Args:
        capabilities: The CAPABILITY_SNAPSHOT dict.
        output_dir: Where to write the table.
        candidates: Optional override for candidate instruments.

    Returns:
        The viability table dict (also written to disk).
    """
    if candidates is None:
        candidates = DEFAULT_CANDIDATES

    # MISSION v4.5.423: Apply Allowlist Override
    override_symbols, override_hash = get_allowlist_override(REPO_ROOT)
    override_applied = False
    if override_symbols:
        print(f"🔓 ALLOWLIST OVERRIDE DETECTED: {override_symbols} (Hash: {override_hash[:8]}...)")
        capabilities["allowlist"] = override_symbols
        override_applied = True

    # MISSION v4.5.424: Identity Warden License Gate
    license_ok, license_msg = _check_license(capabilities)
    if not license_ok:
        print(f"🛑 LICENSE INVALID: Identity Warden has blocked execution. (Reason: {license_msg})")

    instruments: List[Dict[str, Any]] = []
    for candidate in candidates:
        if not license_ok:
            viable, reason = False, LICENSE_INVALID
        else:
            viable, reason = _check_viability(candidate, capabilities)
        
        instruments.append({
            "symbol": candidate["symbol"],
            "asset_class": candidate["asset_class"],
            "viable": viable,
            "reason": reason,
            "short_allowed": capabilities.get("brokers", {}).get(capabilities.get("primary_broker", "ibkr"), {}).get("account_type") != "cash",
            "min_cost_usd": candidate["min_cost_usd"],
            "fractional": candidate["fractional"],
        })

    # Summary counts
    viable_count = sum(1 for i in instruments if i["viable"])
    blocked_count = len(instruments) - viable_count

    table: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "instruments": instruments,
        "summary": {
            "total_candidates": len(instruments),
            "viable": viable_count,
            "blocked": blocked_count,
            "buying_power_usd": capabilities.get("buying_power_cash_usd", 0),
        },
        "trader_ops_version": get_version_str(),
        "TRADER_OPS_PROMPT_ID": os.environ.get("TRADER_OPS_PROMPT_ID", "UNSET"),
        "allowlist_override_applied": override_applied,
        "override_sha256": override_hash,
    }

    out_path = output_dir / "INSTRUMENT_VIABILITY_TABLE.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(table, f, indent=2, sort_keys=False)

    print(f"📊 Viability Table: {viable_count} viable, {blocked_count} blocked → {out_path.name}")
    for inst in instruments:
        status = "✅" if inst["viable"] else "❌"
        print(f"   {status} {inst['symbol']:6s} ({inst['asset_class']:7s}) — {inst['reason']}")

    return table


def select_viable_smoke_universe(
    viability_table: Dict[str, Any],
    output_dir: Optional[str | Path] = None,
) -> List[str]:
    """
    Select the first viable asset class in priority order.

    Priority: ETF → equity → crypto

    Returns:
        List of viable symbols from the highest-priority viable class.
    """
    instruments = viability_table.get("instruments", [])

    for asset_class in ASSET_CLASS_PRIORITY:
        viable_in_class = [
            i["symbol"]
            for i in instruments
            if i["asset_class"] == asset_class and i["viable"]
        ]
        if viable_in_class:
            print(f"🎯 Smoke Universe: {asset_class.upper()} → {viable_in_class}")
            
            # MISSION v4.7.1: Emit UniverseDecision.json
            decision = {
                "selected_asset_class": asset_class,
                "selected_symbols": viable_in_class,
                "reason": f"Auto-pivoted to {asset_class} based on capital/viability priority.",
                "buying_power_usd": viability_table.get("summary", {}).get("buying_power_usd", 0)
            }
            if output_dir:
                out_path = Path(output_dir) / "DECISION_TRACE.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(decision, f, indent=2)
                print(f"⚖️  Decision Trace Locked: {out_path.name}")

            return viable_in_class

    print("⚠️  No viable smoke universe found!")
    return []
