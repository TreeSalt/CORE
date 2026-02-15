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
from pathlib import Path

def _openssl_verify_ed25519(pub_pem: Path, msg: Path, sig: Path) -> None:
    """Verify Ed25519 signature using OpenSSL (no extra Python deps)."""
    import subprocess
    cmd = [
        "openssl", "pkeyutl", "-verify", "-rawin",
        "-pubin", "-inkey", str(pub_pem),
        "-in", str(msg),
        "-sigfile", str(sig),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"Signature verify failed (openssl): {err}")

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

def base_semver(v: str) -> str:
    """
    Accept either:
      4.4.37
      4.4.37+gb265b02   (PEP440 local / git describe-like)
    Returns the base semver (X.Y.Z) or "".
    """
    m = re.match(r'^(\d+\.\d+\.\d+)', (v or "").strip())
    return m.group(1) if m else ""

def parse_canon_fields(canon_text: str) -> Tuple[str, str, str]:
    mv = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', canon_text)
    mh = re.search(r'fingerprint_sha256:\s*"([a-f0-9]{64})"', canon_text)
    mp = re.search(r'sovereign_pubkey_sha256:\s*"([a-f0-9]{64})"', canon_text)
    return (mv.group(1) if mv else ""), (mh.group(1) if mh else ""), (mp.group(1) if mp else "")

def read_drop_packet_sha256_txt(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse DROP_PACKET_SHA256*.txt.

    Accepts either:
      <sha256>
      <sha256>  <filename>

    Returns (sha256_or_None, filename_or_None).
    """
    if not os.path.exists(path):
        return (None, None)
    try:
        raw = Path(path).read_text(encoding="utf-8").strip()
        if not raw:
            return (None, None)
        parts = raw.split()
        sha = parts[0].strip().lower()
        name = parts[1].strip() if len(parts) >= 2 else None
        if re.fullmatch(r"[0-9a-f]{64}", sha):
            return (sha, name)
    except Exception:
        pass
    return (None, None)

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
    
    # 0.0 Auto-discover sidecar in strict mode (verifier rule, fail-closed).
    if args.strict and not args.drop_packet_sha:
        drop_path = Path(args.drop).resolve()
        drop_dir = drop_path.parent
        m = re.search(r"v(\d+\.\d+\.\d+)", drop_path.name)
        ver = m.group(1) if m else None
        candidates: List[Path] = []
        if ver:
            candidates.append(drop_dir / f"DROP_PACKET_SHA256_v{ver}.txt")
        candidates.append(drop_dir / (drop_path.name + ".sha256"))
        candidates.append(drop_dir / "DROP_PACKET_SHA256.txt")
        for c in candidates:
            if c.exists():
                args.drop_packet_sha = str(c)
                print(f"🔍 Auto-discovered sidecar: {c.name}")
                break
    
    # 0. Legacy Sidecar Gate (Timeline Sovereignty)
    if args.drop_packet_sha:
        sidecar_sha, sidecar_name = read_drop_packet_sha256_txt(args.drop_packet_sha)
        if not sidecar_sha:
            issues.append(Issue(FAIL, "DROP_PACKET_SHA_UNPARSEABLE", "Sidecar unparseable or missing"))
        elif sidecar_sha != drop_sha:
            issues.append(Issue(FAIL, "DROP_PACKET_SHA_MISMATCH", f"Sidecar({sidecar_sha[:8]}) != Actual({drop_sha[:8]})"))
        elif args.strict:
            # Strict: enforce filename match to kill timeline drift forever.
            if sidecar_name is None:
                issues.append(Issue(FAIL, "DROP_PACKET_NAME_MISSING",
                                    "Sidecar must include drop filename in strict mode: '<sha256> <filename>'"))
            else:
                want_name = Path(sidecar_name).name
                got_name = Path(args.drop).name
                if want_name != got_name:
                    issues.append(Issue(FAIL, "DROP_PACKET_NAME_MISMATCH",
                                        f"Sidecar names {want_name} but drop is {got_name}"))
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
                
                # [STAGE 1 FIX: Paradox Resolve] Calculate fingerprint EXCLUDING the canon itself
                # This allow the canon to bind the rest of the manifest without circularity.
                # We save a copy to modify
                pm_fingerprint_obj = pm_obj.copy()
                if "file_sha256" in pm_fingerprint_obj:
                    pm_fingerprint_obj["file_sha256"] = pm_fingerprint_obj["file_sha256"].copy()
                    pm_fingerprint_obj["file_sha256"].pop("docs/ready_to_drop/COUNCIL_CANON.yaml", None)
                
                manifest_sha = canonical_manifest_sha(pm_fingerprint_obj)
                # Canon
                canon_txt = cz.read("docs/ready_to_drop/COUNCIL_CANON.yaml").decode("utf-8")
                c_ver, c_finger, c_pub_pinned = parse_canon_fields(canon_txt)
                if c_ver != version:
                    issues.append(Issue(FAIL, "VERSION_MISMATCH", f"Code:{version} != Canon:{c_ver}"))
                if c_finger != manifest_sha:
                    issues.append(Issue(FAIL, "CANON_BNDING_FAIL", "Canon does not bind manifest hash"))

                # 0.1 Anti-Mimic Gate (Institutional Gold)
                code_zip_names = {n for n in cz.namelist() if not n.endswith("/")}
                
                # --- HYDRA GUARD: Unicode Homoglyph Detection (Vector 80) - Code Zip ---
                for name in code_zip_names:
                    if any(ord(char) > 127 for char in name):
                        issues.append(Issue(FAIL, "HOMOGLYPH_DETECTED_CODE", f"Non-ASCII character in code filename '{name}'"))

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
                # Canonical smoke roots (support both; strict requires exactly one canonical root)
                roots = [
                    "reports/forge/smoke_test",
                    "reports/forge/synthetic_smoke",
                ]
                present_roots = []
                for r in roots:
                    if f"{r}/RUN_METADATA.json" in e_names:
                        present_roots.append(r)

                # --- HYDRA GUARD: Unicode Homoglyph Detection (Vector 80) - Evidence Zip ---
                for name in e_names:
                    # Check for non-ASCII characters that might mimic ASCII (basic check)
                    if any(ord(c) > 127 for c in name):
                        issues.append(Issue(FAIL, "HOMOGLYPH_DETECTED_EVIDENCE", f"Non-ASCII character in evidence filename '{name}'"))

                # --- HYDRA GUARD: Omega Gate Self-Verification (Vector 100) ---
                # Final safety: The verifier checks its own integrity if possible
                # (Mocked for this stage, in reality it would compare against a signed manifest)

                if not present_roots:
                    issues.append(Issue(FAIL, "SMOKE_ROOT_MISSING",
                                       "No smoke root found. Expected RUN_METADATA.json under smoke_test or synthetic_smoke."))
                elif args.strict and len(present_roots) != 1:
                    issues.append(Issue(FAIL, "SMOKE_ROOT_AMBIGUOUS_STRICT",
                                       f"Strict: multiple smoke roots found: {present_roots}"))

                smoke_root = present_roots[0] if present_roots else None
                evidence_root = smoke_root

                # Required trace under selected root
                if smoke_root and f"{smoke_root}/router_trace.csv" not in e_names:
                    issues.append(Issue(FAIL, "ROUTER_TRACE_MISSING", f"{smoke_root}/router_trace.csv missing"))

                # Run metadata
                rm_path = f"{smoke_root}/RUN_METADATA.json" if smoke_root else None
                if not rm_path or rm_path not in e_names:
                    issues.append(Issue(FAIL, "RUN_METADATA_MISSING", "RUN_METADATA.json missing in selected smoke root"))
                else:
                    rm = json.loads(ez.read(rm_path).decode("utf-8", errors="replace"))

                    ev_ver = rm.get("trader_ops_version", "")
                    # Strict: base semver must match; recommend exact match as policy
                    if version and base_semver(ev_ver) != base_semver(version):
                        issues.append(Issue(FAIL, "EVIDENCE_VERSION_DRIFT",
                                           f"evidence={ev_ver} (base={base_semver(ev_ver)}) != code={version} (base={base_semver(version)})"))

                    if code_sha and rm.get("code_hash") != code_sha:
                        issues.append(Issue(FAIL, "EVIDENCE_CODE_HASH_MISMATCH",
                                           f"RUN_METADATA.code_hash={rm.get('code_hash')} != code_zip_sha={code_sha}"))

                    if manifest_sha and rm.get("manifest_hash") != manifest_sha:
                        issues.append(Issue(FAIL, "EVIDENCE_MANIFEST_HASH_MISMATCH",
                                           f"RUN_METADATA.manifest_hash={rm.get('manifest_hash')} != manifest_sha={manifest_sha}"))

                if smoke_root and f"{smoke_root}/router_trace.csv" in e_names:
                    trace = ez.read(f"{smoke_root}/router_trace.csv").decode("utf-8").strip().split("\n")
                    if len(trace) < 5:  # Arbitrary but reasonable for a real smoke test
                        issues.append(Issue(FAIL, "EVIDENCE_TRIVIAL", f"router_trace.csv only has {len(trace)} lines (skeletal)"))

                # Tier 1: Evidence Manifest
                if smoke_root and f"{smoke_root}/EVIDENCE_MANIFEST.json" not in e_names:
                    issues.append(Issue(FAIL, "EVIDENCE_MANIFEST_MISSING", "Tier 1: EVIDENCE_MANIFEST.json missing"))
                else:
                    man_path = f"{smoke_root}/EVIDENCE_MANIFEST.json"
                    if man_path in e_names:
                        em_txt = ez.read(man_path).decode("utf-8")
                        em = json.loads(em_txt)
                        # Verify Git Context Binding
                        if em.get("environment", {}).get("git_commit") == "UNKNOWN":
                            issues.append(Issue(FAIL, "GIT_PROVENANCE_MISSING", "Evidence environment has UNKNOWN git commit"))
                        evidence_git_commit = em.get("environment", {}).get("git_commit")
                
                # Tier 1: Data Manifest
                if smoke_root and f"{smoke_root}/DATA_MANIFEST.json" not in e_names:
                    issues.append(Issue(FAIL, "DATA_MANIFEST_MISSING", "Tier 1: DATA_MANIFEST.json missing"))
                else:
                    dm_path = f"{smoke_root}/DATA_MANIFEST.json"
                    if dm_path in e_names:
                        dm_txt = ez.read(dm_path).decode("utf-8")
                        dm = json.loads(dm_txt)
                        dm_root = dm.get("merkle_root_sha256")
                        if not dm_root:
                            issues.append(Issue(FAIL, "DATA_MANIFEST_INVALID", "Data Manifest missing merkle root"))
                        evidence_data_hash = dm_root

                # Tier 2: Fiduciary Seal (Certificate)
                cert_path = "reports/certification/CERTIFICATE.json"
                sig_path = "reports/certification/CERTIFICATE.json.sig"
                
                if cert_path not in e_names:
                    issues.append(Issue(FAIL, "CERTIFICATE_MISSING", "Fiduciary Certificate missing from evidence"))
                else:
                    cert_json = json.loads(ez.read(cert_path).decode("utf-8"))
                    if args.strict and cert_json.get("strict_mode") is not True:
                         issues.append(Issue(FAIL, "CERTIFICATE_NOT_STRICT", "Certificate strict_mode != true"))
                
                if sig_path not in e_names:
                     issues.append(Issue(FAIL, "SIGNATURE_MISSING", "Certificate Signature missing"))
                
                # Check for Public Key Sovereignty (Independent Verification)
                pub_path = "reports/certification/sovereign.pub"
                if pub_path not in e_names:
                     issues.append(Issue(FAIL, "PUBKEY_MISSING", "Sovereign Public Key missing for verification"))
                elif c_pub_pinned:
                    # Pinned Sovereignty Check
                    got_pub_sha = sha256_bytes(ez.read(pub_path))
                    if got_pub_sha != c_pub_pinned:
                        issues.append(Issue(FAIL, "PUBKEY_PIN_MISMATCH", 
                                           f"Evidence pubkey ({got_pub_sha[:8]}) != Pinned in Code ({c_pub_pinned[:8]})"))
                    else:
                        print(f"✅ Public Key Verified (Pinned: {c_pub_pinned[:8]})")
                
                if args.strict and cert_path in e_names and sig_path in e_names and pub_path in e_names:
                    # Cryptographically verify CERTIFICATE.json.sig (Ed25519) using OpenSSL.
                    try:
                        import tempfile
                        with tempfile.TemporaryDirectory() as td:
                            temp_dir = Path(td)
                            p_pub = temp_dir / "sovereign.pub"
                            p_msg = temp_dir / "CERTIFICATE.json"
                            p_sig = temp_dir / "CERTIFICATE.json.sig"
                            p_pub.write_bytes(ez.read(pub_path))
                            p_msg.write_bytes(ez.read(cert_path))
                            p_sig.write_bytes(ez.read(sig_path))
                            _openssl_verify_ed25519(p_pub, p_msg, p_sig)
                    except Exception as e:
                        issues.append(Issue(FAIL, "CERT_SIGNATURE_INVALID", str(e)))

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

        # --- HYDRA GUARD: Metadata Shadowing Detection (Vector 40) ---
        if "METADATA.txt" in names and inner_ledger_name:
            # Check if METADATA.txt version matches Ledger version
            meta_txt = drop_zf.read("METADATA.txt").decode("utf-8")
            m_ver = re.search(r"Version:\s*(\d+\.\d+\.\d+)", meta_txt)
            if m_ver and inner_ledger_name:
                ledger_ver = re.search(r"v(\d+\.\d+\.\d+)", inner_ledger_name)
                if ledger_ver and m_ver.group(1) != ledger_ver.group(1):
                     issues.append(Issue(FAIL, "METADATA_SHADOW_DETECTED",
                                        f"METADATA.txt version ({m_ver.group(1)}) != Ledger version ({ledger_ver.group(1)})"))

    # --- Outer Ledger (if provided)
    if args.run_ledger:
        with open(args.run_ledger) as f:
            outer = json.load(f)
        if outer.get("artifacts", {}).get("ready_to_drop", {}).get("sha256") != drop_sha:
            issues.append(Issue(FAIL, "OUTER_LEDGER_DROP_HASH_MISMATCH", f"Outer({outer.get('artifacts', {}).get('ready_to_drop', {}).get('sha256')[:8]}) != Actual({drop_sha[:8]})"))
        
        # [STAGE 1 FIX] Enforce Outer Ledger Version Match
        outer_ver = outer.get("version", "")
        if version and outer_ver != version:
             issues.append(Issue(FAIL, "OUTER_LEDGER_VERSION_MISMATCH", f"OuterLedger({outer_ver}) != InnerCode({version})"))
        
        # Strict Coherence: Ledger must match build environment
        if args.strict and outer.get("strict_mode") is not True:
             issues.append(Issue(FAIL, "LEDGER_NOT_STRICT", "Outer Ledger strict_mode != true"))

        if args.strict:
            sb = outer.get("sovereign_binding") or {}
            if sb.get("git_dirty") is True:
                issues.append(Issue(FAIL, "GIT_DIRTY_STRICT",
                                    "sovereign_binding.git_dirty must be false in --strict mode"))
            git_commit = (sb.get("git_commit") or "").strip()
            if not re.fullmatch(r"[0-9a-f]{7,40}", git_commit):
                issues.append(Issue(FAIL, "GIT_COMMIT_MISSING",
                                    "sovereign_binding.git_commit missing/invalid in --strict mode"))
            ts = outer.get("timestamp_utc")
            if ts in (None, "", "2020-01-01T00:00:00Z", "1970-01-01T00:00:00Z"):
                issues.append(Issue(FAIL, "TIMESTAMP_PLACEHOLDER",
                                    f"timestamp_utc placeholder/empty in --strict mode: {ts!r}"))
            wc = outer.get("build_wallclock_utc")
            if wc in ("2020-01-01T00:00:00Z", "1970-01-01T00:00:00Z"):
                issues.append(Issue(FAIL, "WALLCLOCK_PLACEHOLDER",
                                    f"build_wallclock_utc placeholder in --strict mode: {wc!r}"))

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
