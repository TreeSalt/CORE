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

from antigravity_harness.artifacts import ArtifactManager
from antigravity_harness.utils import get_version_str


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


def format_gate_results(gate_results: List[Dict[str, Any]]) -> str:
    lines = []
    for g in gate_results:
        lines.append(f"{g['gate']}: {g['status']} — {g['reason']}")
    return "\n".join(lines)


def save_run_metadata(
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

    # 4. Data Hash
    data_hash = extra.get("data_hash", "N/A") if extra else "N/A"

    # 5. Fixed Timestamp
    timestamp = pd.Timestamp.now("UTC").isoformat()
    if release_mode:
        timestamp = "2020-01-01T00:00:00Z"

    # 6. Deterministic Run ID
    run_id = uuid.uuid4().hex
    if release_mode and code_hash != "UNKNOWN":
        combined = f"{code_hash}:{config_hash}"
        run_id = f"RUN-{hashlib.sha256(combined.encode()).hexdigest()[:12]}"

    extra_safe = extra or {}
    meta = {
        "run_id": extra_safe.get("run_id", run_id),
        "timestamp_utc": timestamp,
        "trader_ops_version": version_str,
        "code_hash": code_hash,
        "config_hash": config_hash,
        "data_hash": data_hash,
        "cmd_args": cmd_args or {},
        "config_snapshot": config,
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
