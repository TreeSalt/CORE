from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

from mantis_core.artifacts import ArtifactManager
from mantis_core.paths import REPO_ROOT
from mantis_core.utils import get_version_str


def save_artifacts(output_dir: str, name: str, payload: Dict[str, Any], overwrite: bool = False) -> None:
    # Instantiate Warden
    am = ArtifactManager(Path(output_dir))

    base_name = name
    yaml_rel = f"{base_name}.yaml"
    json_rel = f"{base_name}.json"

    # Collision check strategy
    if not overwrite and (am.get_abs_path(yaml_rel).exists() or am.get_abs_path(json_rel).exists()):
        run_id = uuid.uuid4().hex[:8]
        base_name = f"{name}_{run_id}"
        yaml_rel = f"{base_name}.yaml"
        json_rel = f"{base_name}.json"

    # Write via ArtifactManager (Atomic & Hashed)
    # We use overwrite=True because we handled collision logic above or explicitly requested overwrite
    am.write_json(json_rel, payload, overwrite=True)

    # YAML support is not native to ArtifactManager (yet), so we write text
    # or we adhere to "JSON is the Sovereign Format" and maybe drop YAML?
    # The prompt says "save_yaml" imported from config.
    # Let's read config.save_yaml to see if we can route it.
    # For now, let's just write JSON via AM as the primary evidence.
    # We will keep YAML for humans but maybe outside AM or add write_yaml to AM?
    # Adding write_yaml to AM is better. But I can't edit AM right now without context switching.
    # I will stick to writing JSON via AM.
    # And manually writing YAML via AM.write_text.
    yaml_content = yaml.dump(payload, sort_keys=False)
    am.write_text(yaml_rel, yaml_content, overwrite=True)


def generate_no_trade_report(
    output_dir: str,
    router_desired_weights: Dict[str, float],
    fills_count: int,
    capital: float,
    reason: str,
    extra: Dict[str, Any] | None = None,
    status: str = "SMOKE_NO_TRADE",
) -> None:
    """
    MISSION v4.5.339: No-Trade Intelligence.
    If the router desired exposure but physics/capital prevented fills,
    emit a structured NO_TRADE_REPORT.json explaining the primary cause.
    """
    am = ArtifactManager(Path(output_dir))

    report = {
        "status": status,
        "diagnosis": {
            "primary_cause": reason,
            "fills_count": fills_count,
            "capital_usd": capital,
            "router_desired_weights": router_desired_weights,
            "explanation": (
                f"Router desired non-zero exposure across "
                f"{len([w for w in router_desired_weights.values() if w > 0])} assets, "
                f"but {fills_count} fills were executed. "
                f"Primary cause: {reason}."
            ),
        },
        "timestamp_utc": pd.Timestamp.now("UTC").isoformat(),
        "trader_ops_version": get_version_str(),
        "TRADER_OPS_PROMPT_ID": os.environ.get("TRADER_OPS_PROMPT_ID", "UNSET"),
    }
    if extra:
        report["diagnosis"].update(extra)

    am.write_json("NO_TRADE_REPORT.json", report, overwrite=True)


def generate_trade_proposal(
    output_dir: str,
    symbols: List[str],
    desired_weights: Dict[str, float],
    capital: float,
    strategy_name: str = "unknown",
    broker: str = "ibkr",
    authorized: bool = False,
    mode: str = "assisted",
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    MISSION v4.5.350: Assisted Trader Mode — Trade Proposal.
    Generates TRADE_PROPOSAL.md showing what would be traded
    and whether execution is authorized.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = pd.Timestamp.now("UTC").isoformat()
    version = get_version_str()
    prompt_id = os.environ.get("TRADER_OPS_PROMPT_ID", "UNSET")
    auth_status = "✅ AUTHORIZED" if authorized else "🚫 PENDING — requires --authorize"

    lines = [
        "# TRADE PROPOSAL",
        "",
        f"> **Mode:** `{mode.upper()}`  ",
        f"> **Authorization:** {auth_status}  ",
        f"> **Timestamp:** {timestamp}  ",
        f"> **Strategy:** `{strategy_name}`  ",
        f"> **Broker:** `{broker}`  ",
        f"> **Capital:** ${capital:,.2f}  ",
        f"> **Version:** {version}  ",
        f"> **Prompt ID:** {prompt_id}  ",
        "",
        "## Proposed Orders",
        "",
        "| Symbol | Side | Target Weight | Est. Value | Est. Qty | % of Capital |",
        "|--------|------|---------------|------------|----------|-------------|",
    ]

    for sym in symbols:
        weight = desired_weights.get(sym, 0.0)
        est_value = capital * weight
        # Rough quantity estimate (assume ~$500/share for ETFs, context-dependent)
        est_qty = est_value / 500.0 if est_value > 0 else 0.0
        side = "BUY" if weight > 0 else "HOLD"
        pct = weight * 100
        lines.append(
            f"| {sym} | {side} | {weight:.4f} | ${est_value:,.2f} | ~{est_qty:.2f} | {pct:.1f}% |"
        )

    lines.extend([
        "",
        "## Risk Summary",
        "",
        f"- **Total Intended Exposure:** {sum(desired_weights.values()) * 100:.1f}%",
        f"- **Cash Reserve:** ${capital * (1 - sum(desired_weights.values())):,.2f}",
        f"- **Max Single Position:** {max(desired_weights.values()) * 100:.1f}% (${capital * max(desired_weights.values()):,.2f})",
        "",
        "## Authorization Gate",
        "",
    ])

    if authorized:
        lines.append("Orders are **AUTHORIZED** for execution. Proceeding to simulation.")
    else:
        lines.extend([
            "Orders are **BLOCKED**. To authorize execution, re-run with `--authorize`:",
            "",
            "```bash",
            "python3 -m mantis_core.cli portfolio-backtest ... --authorize",
            "```",
            "",
            "> [!CAUTION]",
            "> No orders will be transmitted without explicit authorization.",
        ])

    lines.append("")

    proposal_path = out_path / "TRADE_PROPOSAL.md"
    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also emit JSON sidecar for machine consumption
    am = ArtifactManager(Path(output_dir))
    proposal_json = {
        "mode": mode,
        "authorized": authorized,
        "symbols": symbols,
        "desired_weights": desired_weights,
        "capital_usd": capital,
        "strategy": strategy_name,
        "broker": broker,
        "intended_exposure_pct": sum(desired_weights.values()) * 100.0,
        "timestamp_utc": timestamp,
        "trader_ops_version": version,
        "TRADER_OPS_PROMPT_ID": prompt_id,
    }
    if extra:
        proposal_json.update(extra)
    am.write_json("TRADE_PROPOSAL.json", proposal_json, overwrite=True)

    print(f"📋 Trade Proposal: {proposal_path.name} ({auth_status})")


def format_gate_results(gate_results: List[Dict[str, Any]]) -> str:
    lines = []
    for g in gate_results:
        lines.append(f"{g['gate']}: {g['status']} — {g['reason']}")
    return "\n".join(lines)


def save_run_metadata( # noqa: PLR0912, PLR0915
    output_dir: str,
    config: Dict[str, Any],
    cmd_args: Dict[str, Any] | None = None,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Phase 12: The Metadata Lock.
    Saves RUN_METADATA.json via ArtifactManager.
    Mandatory for every run.
    """
    am = ArtifactManager(Path(output_dir))

    # MISSION v4.5.382: Sealing the Active Tape Manifest
    manifest_path = Path(output_dir) / "ACTIVE_TAPE_MANIFEST.json"
    manifest_hash = "N/A"
    if manifest_path.exists():
        manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    # MISSION v4.5.382: Allowlist Override Binding
    override_path = Path(REPO_ROOT) / "ALLOWLIST_OVERRIDE.json"
    override_hash = "N/A"
    if override_path.exists():
        override_hash = hashlib.sha256(override_path.read_bytes()).hexdigest()

    # Mandate 2: Deterministic Metadata
    release_mode = os.environ.get("METADATA_RELEASE_MODE") == "1"

    # 1. Version
    version_str = get_version_str()

    # 2. Config Hash
    cfg_str = json.dumps(config, sort_keys=True, default=str)
    config_hash = hashlib.sha256(cfg_str.encode("utf-8")).hexdigest()

    # 3. Code Hash (Priority: Env Var > Git > UNKNOWN)
    code_hash = os.environ.get("METADATA_CODE_HASH")
    if not code_hash:
        try:
            code_hash = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
            )
        except Exception:
            code_hash = "UNKNOWN"

    # 4. Data Hash(es)
    extra_safe = extra or {}
    status = extra_safe.get("status", "UNKNOWN")
    data_hash = extra_safe.get("data_hash")
    if not data_hash or data_hash == "N/A":
        # MISSION v4.7.1: Fail-closed on N/A hashes in Release Mode
        if release_mode:
             raise RuntimeError("FAIL-CLOSED: data_hash is 'N/A' or missing in release mode.")
        data_hash = "N/A"

    is_data_hash = extra_safe.get("is_data_hash", "N/A")
    oos_data_hash = extra_safe.get("oos_data_hash", "N/A")

    # MISSION v4.7.1: Synthetic Honesty
    # Path heuristics: If prices_csv contains "synthetic", force synthetic: True
    synthetic = extra_safe.get("synthetic", False)
    prices_csv = cmd_args.get("prices_csv", "") if cmd_args else ""
    if "synthetic" in str(prices_csv).lower():
        synthetic = True
        print(f"🔬 SYNTHETIC HEURISTIC: {prices_csv} contains 'synthetic'. Forcing synthetic=True.")

    # 5. Real Timestamp — MISSION v4.5.332: No more 2020 stub
    timestamp = pd.Timestamp.now("UTC").isoformat()

    # 6. Deterministic Run ID
    run_id = uuid.uuid4().hex
    if release_mode and code_hash != "UNKNOWN":
        combined = f"{code_hash}:{config_hash}"
        run_id = f"RUN-{hashlib.sha256(combined.encode()).hexdigest()[:12]}"

    # MISSION v4.5.339: Dynamic Prompt ID Binding
    prompt_id = os.environ.get("TRADER_OPS_PROMPT_ID", "UNSET")

    # MISSION v4.5.382: Low-Sample Metrics Tagging
    # If fills < 30, tag metrics as invalid to prevent statistical hallucinations.
    # We look for fills_count in extra or cmd_args
    fills_count = extra_safe.get("fills_count")
    if fills_count is None:
        # Try to infer from results.csv if it exists
        results_path = Path(output_dir) / "results.csv"
        if results_path.exists():
            try:
                df = pd.read_csv(results_path)
                if not df.empty:
                    fills_count = int(df["fills_count"].iloc[0])
            except Exception:
                pass

    metrics_valid = True
    if fills_count is not None and fills_count < 30:
        metrics_valid = False
        print(f"⚠️  LOW SAMPLE DETECTED ({fills_count} fills). Tagging metrics as valid=False.")

    # MISSION v4.7.2: Fail-closed on missing N/A hashes
    mh = extra_safe.get("manifest_sha256", "N/A")
    pmh = extra_safe.get("payload_manifest_sha256", "N/A")
    if release_mode:
        if mh == "N/A":
             raise RuntimeError("FAIL-CLOSED: manifest_sha256 is 'N/A' in release mode.")
        if pmh == "N/A":
             raise RuntimeError("FAIL-CLOSED: payload_manifest_sha256 is 'N/A' in release mode.")
    
    # MISSION v4.7.2: Mandate Decision Trace & Viability Table
    dt_path = Path(output_dir) / "DECISION_TRACE.json"
    vt_path = Path(output_dir) / "INSTRUMENT_VIABILITY_TABLE.json"
    if release_mode:
        if not dt_path.exists():
             raise RuntimeError(f"FAIL-CLOSED: Mandated artifact {dt_path.name} missing.")
        if not vt_path.exists():
             raise RuntimeError(f"FAIL-CLOSED: Mandated artifact {vt_path.name} missing.")

    # MISSION v4.7.1: RUN_METADATA Schema Unification
    meta = {
        "schema_version": "1.0.0",
        "run_id": extra_safe.get("run_id", run_id),
        "timestamp_utc": timestamp,
        "trader_ops_version": version_str,
        "version": version_str, # Redundancy for back-compat
        "TRADER_OPS_PROMPT_ID": prompt_id,
        "metrics_valid": metrics_valid,
        "metrics_invalid_reason": "LOW_SAMPLE" if not metrics_valid else ("SYNTHETIC_DATA" if synthetic else None),
        "synthetic": synthetic,
        "status": status,
        "cmd_args": cmd_args or {},
        "active_tape_manifest_sha256": manifest_hash,
        "manifest_sha256": mh,
        "payload_manifest_sha256": pmh,
        "charter_id": "TRADER_OPS_PROMPT_CHARTER_v2.0",
        
        # Legacy/Extra fields
        "code_hash": code_hash,
        "config_hash": config_hash,
        "data_hash": data_hash,
        "active_tape_manifest_hash": manifest_hash,
        "allowlist_override_hash": override_hash,
        "is_data_hash": is_data_hash,
        "oos_data_hash": oos_data_hash,
        "config_snapshot": config,
        "certification_fingerprint": hashlib.sha256(cfg_str.encode("utf-8")).hexdigest(),
        "environment_vars": {
            "PYTHONPATH": os.environ.get("PYTHONPATH", "UNDEFINED"),
            "METADATA_RELEASE_MODE": os.environ.get("METADATA_RELEASE_MODE", "0"),
        },
        **extra_safe,
    }

    # Atomic Write: Write to temp, then rename
    tmp_path = am.get_abs_path("RUN_METADATA.json.tmp")
    final_path = am.get_abs_path("RUN_METADATA.json")
    
    with open(tmp_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(tmp_path, final_path)


def generate_walkforward_report(
    output_dir: str,
    oos_metrics: Dict[str, Any],
    oos_fills_count: int,
    oos_intended_exposure_bars: int,
    oos_pf: float,
) -> str:
    """
    MISSION v4.5.360: OOS Promotion Edge Cases.
    Returns the final status string.
    """
    am = ArtifactManager(Path(output_dir))
    
    status = "PASS_OOS"
    reason = "OOS performance within tolerance."
    
    # 1. Zero-fill Edge Case: intended to trade but physics/market prevented execution
    if oos_fills_count == 0 and oos_intended_exposure_bars > 0:
        status = "FAIL_OOS_NO_TRADE"
        reason = "OOS intended exposure was non-zero, but 0 fills occurred (Potential PF=999 artifact)."
    
    # 2. Degradation Edge Case: performance below break-even
    elif oos_pf < 1.0:
        status = "FAIL_OOS_DEGRADATION"
        reason = f"OOS Profit Factor ({oos_pf:.4f}) < 1.0 baseline."

    report = {
        "status": status,
        "reason": reason,
        "oos_pf": oos_pf,
        "oos_fills": oos_fills_count,
        "oos_exposure_bars": oos_intended_exposure_bars,
        "oos_metrics_snapshot": oos_metrics,
        "timestamp_utc": pd.Timestamp.now("UTC").isoformat(),
    }
    am.write_json("WALKFORWARD_OOS_REPORT.json", report, overwrite=True)
    return status

