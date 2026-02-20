#!/usr/bin/env python3
"""
scripts/council_packet.py
=========================
v4.5.82 - Council Packet Summary Generator.
Aggregates metadata into a deterministic COUNCIL_BRIEF.md.
"""

import hashlib
import json
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = REPO_ROOT / "dist"
SMOKE_REPORT_DIR = REPO_ROOT / "reports" / "forge" / "synthetic_smoke"

def sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("📋 Generating Council Brief...")
    
    # 1. Identify Version
    # We look at antigravity_harness/__init__.py for source version
    init_path = REPO_ROOT / "antigravity_harness" / "__init__.py"
    version = "4.5.82" # Default fallback
    if init_path.exists():
        for line in init_path.read_text().splitlines():
            if "__version__" in line:
                version = line.split('"')[1]
                break

    brief_path = DIST_DIR / f"COUNCIL_BRIEF_v{version}.md"
    
    # 2. Gather Artifact SHAs
    zips = {
        "READY_TO_DROP": DIST_DIR / f"TRADER_OPS_READY_TO_DROP_v{version}.zip",
        "EVIDENCE": DIST_DIR / f"TRADER_OPS_EVIDENCE_v{version}.zip",
        "CODE_ONLY": DIST_DIR / f"TRADER_OPS_CODE_v{version}.zip"
    }
    
    # 3. Load Smoke Test Metadata
    manifest_path = SMOKE_REPORT_DIR / "EVIDENCE_MANIFEST.json"
    prompt_path = SMOKE_REPORT_DIR / "PROMPT_FINGERPRINT.json"
    data_path = SMOKE_REPORT_DIR / "DATA_MANIFEST.json"
    
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    prompt = {}
    if prompt_path.exists():
        with open(prompt_path) as f:
            prompt = json.load(f)

    data = {}
    if data_path.exists():
        with open(data_path) as f:
            data = json.load(f)

    # 4. Compose Markdown
    lines = [
        f"# Council Brief - v{version}",
        f"Generated: {Path('/tmp/now').read_text().strip() if Path('/tmp/now').exists() else '2026-02-19'}",
        "",
        "## Artifact Integrity (SHAs)",
    ]
    
    for label, fpath in zips.items():
        if fpath.exists():
            sha = sha256_file(fpath)
            lines.append(f"- **{label}**: `{sha}`")
        else:
            lines.append(f"- **{label}**: *Not Found*")

    lines.extend([
        "",
        "## Gate Report Summary",
        f"- **Env**: {manifest.get('environment', {}).get('platform', 'N/A')}",
        f"- **Git Commit**: `{manifest.get('environment', {}).get('git_commit', 'N/A')}`",
        "",
        "## Prompt Provenance",
        f"- **Prompt ID**: `{prompt.get('prompt_id', 'N/A')}`",
        f"- **Charter ID**: `{prompt.get('charter_id', 'N/A')}`",
        f"- **Prompt SHA**: `{prompt.get('prompt_sha256', 'N/A')}`",
        "",
        "## Dataset Information",
        f"- **Data Merkle Root**: `{data.get('merkle_root_sha256', 'N/A')}`",
        "- **Dataset Files**:",
    ])
    
    for f in data.get("files", {}):
        lines.append(f"  - `{f}`")

    with open(brief_path, "w") as f:
        f.write("\n".join(lines) + "\n")
        
    print(f"✅ Council Brief Emitted: {brief_path}")

if __name__ == "__main__":
    main()
