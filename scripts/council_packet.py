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

def extract_evidence_data(evidence_zip: Path):
    """Deep forensic extraction of metadata from evidence zip."""
    prompt_info = {}
    data_manifest = {}
    
    with zipfile.ZipFile(evidence_zip, "r") as z:
        # Prompt Fingerprint
        targets = [f for f in z.namelist() if f.endswith("PROMPT_FINGERPRINT.json")]
        if targets:
            try:
                with z.open(targets[0]) as f:
                    prompt_info = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to parse Prompt Fingerprint: {e}")

        # Data Manifest
        targets = [f for f in z.namelist() if f.endswith("DATA_MANIFEST.json")]
        if targets:
            try:
                with z.open(targets[0]) as f:
                    data_manifest = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to parse Data Manifest: {e}")
                
    return prompt_info, data_manifest

def build_gate_report_summary(dist_dir: Path):
    """Analyzes the latest fail-closed gate report."""
    gate_path = dist_dir / "gate_report.json"
    if not gate_path.exists():
        return ["_Gate Report Not Found_"]

    try:
        with open(gate_path, "r") as f:
            gate_report = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ["_Error Reading Gate Report_"]

    gates = gate_report.get("gates", {})
    if not gates:
        return ["_Empty Gate Report_"]

    md = ["| Gate | Status |", "|---|---|"]
    for k, v in gates.items():
        status = "✅ PASS"
        if isinstance(v, dict) and "status" in v:
            status = v["status"]
        elif v is True:
            status = "✅ PASS"
        elif v is False:
            status = "❌ FAIL"
        elif v != "PASS":
            status = f"❓ {v}"
            
        md.append(f"| {k} | {status} |")
    return md

def build_data_manifest_summary(data_manifest: dict, run_ledger: dict = None):
    """Forensic summary of the dataset used in simulation."""
    # Authoritative Data Hash from Ledger if available
    data_hash = "N/A"
    if run_ledger and "sovereign_binding" in run_ledger:
        data_hash = run_ledger["sovereign_binding"].get("data_hash", "N/A")
    elif data_manifest:
        data_hash = data_manifest.get("data_hash", "N/A")

    if not data_manifest and data_hash == "N/A":
        return ["_Data Manifest Not Found in Evidence_"]

    md = [f"- **Data Hash**: `{data_hash}`"]
    files = data_manifest.get("files", {}) if data_manifest else {}
    if not files and data_manifest and "entries" in data_manifest:
         files = data_manifest["entries"]
         
    md.append("**Files**:")
    if isinstance(files, dict):
        for fpath, fhash in files.items():
            md.append(f"- `{fpath}`: `{fhash}`")
    elif isinstance(files, list):
        for f in files:
            md.append(f"- `{f}`")
    return md

def emit_brief(dist_dir: Path):
    """Institutional Grade Council Brief Generation."""
    version, drop_zip = find_newest_version(dist_dir)
    print(f"Generating Council Brief for v{version}...")
    
    evidence_zip = dist_dir / f"TRADER_OPS_EVIDENCE_v{version}.zip"
    code_zip = dist_dir / f"TRADER_OPS_CODE_v{version}.zip"
    run_ledger_path = dist_dir / f"RUN_LEDGER_v{version}.json"
    
    if not evidence_zip.exists():
        fail(f"Evidence Zip missing: {evidence_zip}")

    shas = {
        "drop": sha256_file(drop_zip),
        "code": sha256_file(code_zip) if code_zip.exists() else "MISSING",
        "evidence": sha256_file(evidence_zip),
        "ledger": sha256_file(run_ledger_path) if run_ledger_path.exists() else "MISSING",
    }
    
    run_ledger = None
    if run_ledger_path.exists():
        with open(run_ledger_path, "r") as f:
            run_ledger = json.load(f)

    prompt_info, data_manifest = extract_evidence_data(evidence_zip)
    
    # Markdown Content Construction
    md = [
        f"# Council Brief: v{version}",
        f"**Drop Packet SHA256**: `{shas['drop']}`",
        f"**Code SHA256**: `{shas['code']}`",
        f"**Evidence SHA256**: `{shas['evidence']}`",
        f"**Ledger SHA256**: `{shas['ledger']}`",
        "",
        "## 🛡️ Gate Report Summary"
    ]
    md.extend(build_gate_report_summary(dist_dir))
    md.append("")
    
    md.append("## 🧠 Prompt Provenance")
    if prompt_info:
        md.append(f"- **ID**: `{prompt_info.get('prompt_id', 'N/A')}`")
        md.append(f"- **SHA256**: `{prompt_info.get('prompt_sha256', 'N/A')}`")
    else:
        # Fallback to RUN_LEDGER if possible? Usually not in ledger.
        md.append("_Prompt Info Not Found in Evidence_")
    md.append("")

    md.append("## 💾 Data Manifest")
    md.extend(build_data_manifest_summary(data_manifest, run_ledger))
    md.append("")

    md.append("## 🚢 Execution Bridge Status")
    md.append("- **Mode**: `PAPER-ONLY`")
    md.append("- **Live Trading**: `UNCONDITIONALLY DISABLED` (Fiduciary Lock)")
    md.append("- **Audit Log**: `dist/audit/execution_events_v*.jsonl`")
    md.append("")
        
    out_path = dist_dir / f"COUNCIL_BRIEF_v{version}.md"
    with open(out_path, "w") as f:
        f.write("\n".join(md))
        
    print(f"✅ Council Brief Generated: {out_path}")
    print("\n-- SUMMARY HEAD --")
    print("\n".join(md[:20]))

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
