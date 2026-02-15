#!/usr/bin/env python3
"""
verify_drop_packet.py — Fiduciary Gate Verifier for Institutional Gold.
Exit codes: 0 = PASS, 2 = FAIL.
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

FAIL = "FAIL"
WARN = "WARN"

@dataclass
class Issue:
    level: str
    code: str
    msg: str

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_manifest_sha(manifest_obj: Dict[str, Any]) -> str:
    b = json.dumps(manifest_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def parse_version_from_init(init_text: str) -> str:
    m = re.search(r'__version__\s*=\s*"(\d+\.\d+\.\d+)"', init_text)
    return m.group(1) if m else ""

def parse_canon_fields(canon_text: str) -> Tuple[str, str]:
    mv = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', canon_text)
    mh = re.search(r'fingerprint_sha256:\s*"([a-f0-9]{64})"', canon_text)
    return (mv.group(1) if mv else ""), (mh.group(1) if mh else "")

def read_drop_packet_sha256_txt(path: str) -> Optional[str]:
    """
    Accepts lines like:
      <sha256>
      <sha256>  <filename>
    Returns the sha256 hex string or None if unparseable.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            raw = f.read().strip()
            if not raw:
                return None
            token = raw.split()[0].strip()
            if re.fullmatch(r"[a-f0-9]{64}", token):
                return token
    except Exception:
        pass
    return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", required=True, help="Path to TRADER_OPS_READY_TO_DROP_*.zip")
    ap.add_argument("--run-ledger", default=None, help="Path to outer RUN_LEDGER_vX.Y.Z.json")
    ap.add_argument("--drop-packet-sha", default=None, help="Path to legacy DROP_PACKET_SHA256.txt")
    ap.add_argument("--strict", action="store_true", help="Enable strict semantic gates")
    args = ap.parse_args()

    issues: List[Issue] = []
    print(f"🛡️  Verifying Drop: {args.drop}")

    # --- Load drop zip
    drop_sha = sha256_file(args.drop)
    
    # 0. Legacy Sidecar Gate (Timeline Sovereignty)
    if args.drop_packet_sha:
        sidecar_sha = read_drop_packet_sha256_txt(args.drop_packet_sha)
        if not sidecar_sha:
            issues.append(Issue(FAIL, "DROP_PACKET_SHA_UNPARSEABLE", "Sidecar unparseable or missing"))
        elif sidecar_sha != drop_sha:
            issues.append(Issue(FAIL, "DROP_PACKET_SHA_MISMATCH", f"Sidecar({sidecar_sha[:8]}) != Actual({drop_sha[:8]})"))
    elif args.strict:
        issues.append(Issue(FAIL, "DROP_PACKET_SHA_MISSING_STRICT", "Legacy sidecar required in strict mode"))

    try:
        drop_zf = zipfile.ZipFile(args.drop, "r")
    except Exception as e:
        print(f"❌ FAIL: Could not open drop zip: {e}")
        return 2

    with drop_zf:
        names = set(drop_zf.namelist())

        # Find inner artifacts
        code_candidates = [n for n in names if n.startswith("TRADER_OPS_CODE_") and n.endswith(".zip")]
        evidence_candidates = [n for n in names if n.startswith("TRADER_OPS_EVIDENCE_") and n.endswith(".zip")]
        inner_ledger_candidates = [n for n in names if n.startswith("RUN_LEDGER_INNER_") and n.endswith(".json")]

        if len(code_candidates) != 1:
            issues.append(Issue(FAIL, "CODE_ZIP_MISSING", f"Found: {code_candidates}"))
        code_name = code_candidates[0] if code_candidates else None

        if len(evidence_candidates) != 1:
            issues.append(Issue(FAIL, "EVIDENCE_ZIP_MISSING", f"Found: {evidence_candidates}"))
        evidence_name = evidence_candidates[0] if evidence_candidates else None

        if len(inner_ledger_candidates) != 1:
            issues.append(Issue(FAIL, "INNER_LEDGER_MISSING", f"Found: {inner_ledger_candidates}"))
        inner_ledger_name = inner_ledger_candidates[0] if inner_ledger_candidates else None

        if "METADATA.txt" not in names:
            issues.append(Issue(FAIL, "METADATA_MISSING", "METADATA.txt missing from drop"))

        # --- Inspect CODE
        code_sha = version = manifest_sha = ""
        if code_name:
            c_bytes = drop_zf.read(code_name)
            code_sha = sha256_bytes(c_bytes)
            with zipfile.ZipFile(io.BytesIO(c_bytes)) as cz:
                # Version
                init_txt = cz.read("antigravity_harness/__init__.py").decode("utf-8")
                version = parse_version_from_init(init_txt)
                # Manifest
                pm_raw = cz.read("docs/ready_to_drop/PAYLOAD_MANIFEST.json").decode("utf-8")
                pm_obj = json.loads(pm_raw)
                manifest_sha = canonical_manifest_sha(pm_obj)
                # Canon
                canon_txt = cz.read("docs/ready_to_drop/COUNCIL_CANON.yaml").decode("utf-8")
                c_ver, c_finger = parse_canon_fields(canon_txt)
                if c_ver != version:
                    issues.append(Issue(FAIL, "VERSION_MISMATCH", f"Code:{version} != Canon:{c_ver}"))
                if c_finger != manifest_sha:
                    issues.append(Issue(FAIL, "CANON_BNDING_FAIL", "Canon does not bind manifest hash"))

                # 0.1 Anti-Mimic Gate (Institutional Gold)
                code_zip_names = {n for n in cz.namelist() if not n.endswith("/")}
                manifest_files = set(pm_obj.get("file_sha256", {}).keys())
                # Add known auxiliary files that are NOT in the payload manifest
                manifest_files.add("docs/ready_to_drop/PAYLOAD_MANIFEST.json")
                manifest_files.add("docs/ready_to_drop/COUNCIL_CANON.yaml")
                
                mimics = code_zip_names - manifest_files
                if mimics:
                    issues.append(Issue(FAIL, "CODE_MIMIC_DETECTED", f"Unaccounted files in CODE zip: {list(mimics)}"))

        # --- Inspect EVIDENCE
        evidence_sha = ""
        evidence_git_commit = ""
        evidence_data_hash = ""
        if evidence_name:
            e_bytes = drop_zf.read(evidence_name)
            evidence_sha = sha256_bytes(e_bytes)
            with zipfile.ZipFile(io.BytesIO(e_bytes)) as ez:
                e_names = set(ez.namelist())
                # Stricter audit of evidence suite
                # Evidence Lanes: Allow "synthetic_smoke" OR "smoke_test" (legacy)
                # We check for the new path first
                evidence_root = "reports/forge/synthetic_smoke"
                if f"{evidence_root}/RUN_METADATA.json" not in e_names:
                     # Fallback for older artifacts or if user reverts
                     evidence_root = "reports/forge/smoke_test"

                required_evidence = [
                    f"{evidence_root}/RUN_METADATA.json",
                    f"{evidence_root}/router_trace.csv",
                    f"{evidence_root}/PORTFOLIO_SUMMARY.json",
                    f"{evidence_root}/SUMMARY.md"
                ]
                for r in required_evidence:
                    if r not in e_names:
                        issues.append(Issue(FAIL, "EVIDENCE_SKELETAL", f"Missing mandated evidence: {r}"))

                if f"{evidence_root}/RUN_METADATA.json" in e_names:
                    rm_txt = ez.read(f"{evidence_root}/RUN_METADATA.json").decode("utf-8")
                    rm = json.loads(rm_txt)
                    if not rm.get("trader_ops_version", "").startswith(version):
                        issues.append(Issue(FAIL, "EVIDENCE_VER_DRIFT", f"Ev:{rm.get('trader_ops_version')} != Code:{version}"))
                    if rm.get("code_hash") != code_sha:
                        issues.append(Issue(FAIL, "EVIDENCE_CODE_BINDING_FAIL", "Evidence does not bind actual Code Zip hash"))
                    if rm.get("manifest_hash") != manifest_sha:
                        issues.append(Issue(FAIL, "EVIDENCE_MANIFEST_BINDING_FAIL", "Evidence does not bind Manifest hash"))

                # Row count check for traces
                if f"{evidence_root}/router_trace.csv" in e_names:
                    trace = ez.read(f"{evidence_root}/router_trace.csv").decode("utf-8").strip().split("\n")
                    if len(trace) < 5:  # Arbitrary but reasonable for a real smoke test
                        issues.append(Issue(FAIL, "EVIDENCE_TRIVIAL", f"router_trace.csv only has {len(trace)} lines (skeletal)"))

                # Tier 1: Evidence Manifest
                if f"{evidence_root}/EVIDENCE_MANIFEST.json" not in e_names:
                    issues.append(Issue(FAIL, "EVIDENCE_MANIFEST_MISSING", "Tier 1: EVIDENCE_MANIFEST.json missing"))
                else:
                    em_txt = ez.read(f"{evidence_root}/EVIDENCE_MANIFEST.json").decode("utf-8")
                    em = json.loads(em_txt)
                    # Verify Git Context Binding
                    if em.get("environment", {}).get("git_commit") == "UNKNOWN":
                        issues.append(Issue(FAIL, "GIT_PROVENANCE_MISSING", "Evidence environment has UNKNOWN git commit"))
                    evidence_git_commit = em.get("environment", {}).get("git_commit")
                
                # Tier 1: Data Manifest
                if f"{evidence_root}/DATA_MANIFEST.json" not in e_names:
                    issues.append(Issue(FAIL, "DATA_MANIFEST_MISSING", "Tier 1: DATA_MANIFEST.json missing"))
                else:
                    dm_txt = ez.read(f"{evidence_root}/DATA_MANIFEST.json").decode("utf-8")
                    dm = json.loads(dm_txt)
                    dm_root = dm.get("merkle_root_sha256")
                    if not dm_root:
                        issues.append(Issue(FAIL, "DATA_MANIFEST_INVALID", "Data Manifest missing merkle root"))
                    evidence_data_hash = dm_root

        # --- Inspect INNER LEDGER
        if inner_ledger_name:
            il = json.loads(drop_zf.read(inner_ledger_name).decode("utf-8"))
            if "ready_to_drop" in il.get("artifacts", {}):
                issues.append(Issue(FAIL, "INNER_LEDGER_CIRCULARITY", "Inner ledger contains ready_to_drop hash! (Circular)"))
            
            # Check for Saboteur Node identity
            if il.get("sovereign_binding", {}).get("builder_id") == "SABOTEUR_NODE_01":
                issues.append(Issue(FAIL, "SABOTAGE_ID_DETECTED", "Ledger self-identifies as SABOTEUR_NODE_01"))

            if il.get("artifacts", {}).get("code", {}).get("sha256") != code_sha:
                issues.append(Issue(FAIL, "INNER_LEDGER_CODE_HASH_MISMATCH", f"Inner({il.get('artifacts', {}).get('code', {}).get('sha256')[:8]}) != Actual({code_sha[:8]})"))

            # Tier 1: Ledger Binding Checks
            ledger_data_hash = il.get("sovereign_binding", {}).get("data_hash")
            if ledger_data_hash != evidence_data_hash:
                 issues.append(Issue(FAIL, "DATA_HASH_MISMATCH", f"Ledger({ledger_data_hash[:8]}) != Evidence({evidence_data_hash[:8]})"))
            
            ledger_git = il.get("sovereign_binding", {}).get("git_commit")
            if ledger_git != evidence_git_commit:
                 issues.append(Issue(FAIL, "GIT_COMMIT_MISMATCH", f"Ledger({ledger_git}) != Evidence({evidence_git_commit})"))

            # Tier 1: Drop Preimage (Single-File Sovereignty)
            stored_preimage = il.get("sovereign_binding", {}).get("drop_preimage_sha256")
            if not stored_preimage:
                issues.append(Issue(FAIL, "PREIMAGE_MISSING", "Inner Ledger missing drop_preimage_sha256"))
            else:
                # Re-compute from the artifact block in the ledger itself
                # This ensures the ledger's "artifacts" block wasn't tampered with relative to the binding
                # And since we checked the artifact hashes against real files above, the chain is closed.
                artifacts_block = il.get("artifacts", {})
                # Ensure ready_to_drop is NOT present (it shouldn't be in inner, but just in case)
                if "ready_to_drop" in artifacts_block:
                     # Make a copy to strip it for calculation, though strict gate above fails if it exists
                     artifacts_block = artifacts_block.copy()
                     artifacts_block.pop("ready_to_drop")
                
                b = json.dumps(artifacts_block, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                calc_preimage = hashlib.sha256(b).hexdigest()
                
                if calc_preimage != stored_preimage:
                    issues.append(Issue(FAIL, "PREIMAGE_MISMATCH", f"Stored({stored_preimage[:8]}) != Calc({calc_preimage[:8]})"))

    # --- Outer Ledger (if provided)
    if args.run_ledger:
        with open(args.run_ledger) as f:
            outer = json.load(f)
        if outer.get("artifacts", {}).get("ready_to_drop", {}).get("sha256") != drop_sha:
            issues.append(Issue(FAIL, "OUTER_LEDGER_DROP_HASH_MISMATCH", f"Outer({outer.get('artifacts', {}).get('ready_to_drop', {}).get('sha256')[:8]}) != Actual({drop_sha[:8]})"))

    hard_fails = [i for i in issues if i.level == FAIL]
    if hard_fails:
        print(f"❌ FAIL: {len(hard_fails)} hard gate failures detected.")
        for i in issues:
            print(f"  [{i.level}] {i.code}: {i.msg}")
        return 2
    
    print("✅ PASS: All Fiduciary Gates Secured.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
