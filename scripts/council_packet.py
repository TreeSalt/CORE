#!/usr/bin/env python3
"""
COUNCIL PACKET GENERATOR
Deterministic Evidence Brief from Zip
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

def fail(msg: str):
    print(f"❌ COUNCIL PACKET FATAL: {msg}")
    sys.exit(1)

def find_newest_version(dist_dir: Path):
    candidates = list(dist_dir.glob("TRADER_OPS_READY_TO_DROP_v*.zip"))
    if not candidates:
        fail(f"No drop packets found in {dist_dir}")
    
    # Sort by version via regex (vX.Y.Z)
    pattern = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
    
    def parsable_version(p: Path):
        m = pattern.search(str(p))
        if m:
            return tuple(map(int, m.groups()))
        return (0, 0, 0)

    # Sort descending
    candidates.sort(key=parsable_version, reverse=True)
    best = candidates[0]
    
    m = pattern.search(str(best))
    if not m:
        fail(f"Could not parse version from {best}")
    
    version_str = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
    return version_str, best

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def emit_brief(dist_dir: Path):
    version, drop_zip = find_newest_version(dist_dir)
    print(f"Generating Council Brief for v{version}...")
    
    evidence_zip = dist_dir / f"TRADER_OPS_EVIDENCE_v{version}.zip"
    code_zip = dist_dir / f"TRADER_OPS_CODE_v{version}.zip"
    run_ledger = dist_dir / f"RUN_LEDGER_v{version}.json"
    
    if not evidence_zip.exists():
        fail(f"Evidence Zip missing: {evidence_zip}")

    # Compute artifact SHAs
    shas = {
        "drop": sha256_file(drop_zip),
        "code": sha256_file(code_zip) if code_zip.exists() else "MISSING",
        "evidence": sha256_file(evidence_zip),
        "ledger": sha256_file(run_ledger) if run_ledger.exists() else "MISSING",
    }
    
    # Extract Data from Evidence Zip
    prompt_info = {}
    data_manifest = {}
    gate_report = {}
    
    with zipfile.ZipFile(evidence_zip, "r") as z:
        # Prompt Fingerprint
        try:
            # Look for PROMPT_FINGERPRINT.json
            targets = [f for f in z.namelist() if f.endswith("PROMPT_FINGERPRINT.json")]
            if targets:
                with z.open(targets[0]) as f:
                    prompt_info = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read Prompt Fingerprint: {e}")

        # Data Manifest
        try:
            targets = [f for f in z.namelist() if f.endswith("DATA_MANIFEST.json")]
            if targets:
                with z.open(targets[0]) as f:
                    data_manifest = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read Data Manifest: {e}")

    # Gate Report (usually in dist or maybe inside evidence too?)
    # Supervisors usually write gate_report.json to dist during build.
    # We'll check dist first.
    gate_path = dist_dir / "gate_report.json"
    if gate_path.exists():
        try:
            with open(gate_path, "r") as f:
                gate_report = json.load(f)
        except:
            pass
            
    # Markdown Content
    md = []
    md.append(f"# Council Brief: v{version}")
    md.append(f"**Drop Packet SHA256**: `{shas['drop']}`")
    md.append(f"**Code SHA256**: `{shas['code']}`")
    md.append(f"**Evidence SHA256**: `{shas['evidence']}`")
    md.append(f"**Ledger SHA256**: `{shas['ledger']}`")
    md.append("")
    
    md.append("## 🛡️ Gate Report Summary")
    if gate_report:
        # Pass/Fail + gates
        # Assuming simple structure
        gates = gate_report.get("gates", {})
        md.append("| Gate | Status |")
        md.append("|---|---|")
        for k, v in gates.items():
            status = "✅ PASS" if v else "❌ FAIL" # Simplification
            # If v is a dict with 'status' or just boolean
            if isinstance(v, dict) and "status" in v:
                status = v["status"]
            elif v is True: status = "✅ PASS"
            elif v is False: status = "❌ FAIL"
            
            md.append(f"| {k} | {status} |")
    else:
        md.append("_Gate Report Not Found_")
    md.append("")

    md.append("## 🧠 Prompt Provenance")
    if prompt_info:
        md.append(f"- **ID**: `{prompt_info.get('prompt_id', 'N/A')}`")
        md.append(f"- **SHA256**: `{prompt_info.get('prompt_sha256', 'N/A')}`")
    else:
        md.append("_Prompt Info Not Found in Evidence_")
    md.append("")

    md.append("## 💾 Data Manifest")
    if data_manifest:
        # data_hash + file list
        md.append(f"- **Data Hash**: `{data_manifest.get('data_hash', 'N/A')}`")
        files = data_manifest.get("files", {})
        if not files and "entries" in data_manifest:
             files = data_manifest["entries"]
             
        md.append("**Files**:")
        if isinstance(files, dict):
            for fpath, fhash in files.items():
                md.append(f"- `{fpath}`: `{fhash}`")
        elif isinstance(files, list):
            for f in files:
                md.append(f"- `{f}`")
    else:
        md.append("_Data Manifest Not Found in Evidence_")
        
    # Write to dist
    out_path = dist_dir / f"COUNCIL_BRIEF_v{version}.md"
    with open(out_path, "w") as f:
        f.write("\n".join(md))
        
    print(f"✅ Council Brief Generated: {out_path}")
    print("\n-- SUMMARY HEAD --")
    print("\n".join(md[:15])) # Print head for verification

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_emit = subparsers.add_parser("emit")
    p_emit.add_argument("--dist", default="dist")
    
    args = parser.parse_args()
    
    if args.command == "emit":
        emit_brief(Path(args.dist))

if __name__ == "__main__":
    main()
