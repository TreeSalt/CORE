#!/usr/bin/env python3
"""
scripts/drop_auditor.py
=======================
Institutional-grade verification for TRADER_OPS drop packets.
Scans zips, verifies MANIFEST chain, checks GATES, and emits gate_report.json.
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# sys.path hacking to allow importing antigravity_harness from repo root
REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from antigravity_harness.trust_root import TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256  # noqa: E402

# ANSI Colors for Institutional Output
RED = "\033[31m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class GateResult:
    id: str
    name: str
    status: str  # PASS, FAIL, WARN
    message: str


@dataclass
class GateAccumulator:
    results: List[GateResult] = field(default_factory=list)
    version: str = "UNKNOWN"

    def record(self, gate_id: str, name: str, status: str, message: str):
        self.results.append(GateResult(gate_id, name, status, message))

    def emit_json(self, path: Path):
        data = {
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == "PASS"),
                "failed": sum(1 for r in self.results if r.status == "FAIL"),
                "warned": sum(1 for r in self.results if r.status == "WARN"),
            },
            "gates": [
                {"id": r.id, "name": r.name, "status": r.status, "message": r.message}
                for r in self.results
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"📊 Gate Report Emitted: {path}")


def fail(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"❌ FAIL: {msg}")
    acc.record(gate_id, gate_name, "FAIL", msg)


def ok(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"✅ {msg}")
    acc.record(gate_id, gate_name, "PASS", msg)


def warn(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"⚠️  {msg}")
    acc.record(gate_id, gate_name, "WARN", msg)


def verify_signature(content: bytes, sig_bytes: bytes, pub_path: Path) -> Optional[bool]:
    """Verify Ed25519 signature using openssl pkeyutl."""
    if not pub_path.exists():
        return None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as f_in, \
             tempfile.NamedTemporaryFile(delete=False) as f_sig:
            f_in.write(content)
            f_sig.write(sig_bytes)
            f_in_name = f_in.name
            f_sig_name = f_sig.name

        try:
            # Ed25519 requires pkeyutl -verify -rawin
            # We don't use -sha256 because Ed25519 is implicitly raw/pure or handled by openssl
            subprocess.check_call(
                ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(pub_path), 
                 "-rawin", "-in", f_in_name, "-sigfile", f_sig_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        finally:
            if os.path.exists(f_in_name):
                os.remove(f_in_name)
            if os.path.exists(f_sig_name):
                os.remove(f_sig_name)

    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return False


def _scan_manifest(zf: zipfile.ZipFile, manifest_data: dict, inner_zf: Optional[zipfile.ZipFile], acc: GateAccumulator) -> bool:
    """Scan all files listed in manifest against the zip contents."""
    files = manifest_data.get("file_sha256", {})
    m_ok = True
    namelist = zf.namelist()
    inner_namelist = inner_zf.namelist() if inner_zf else []

    for p, expected in files.items():
        actual = None
        if p in namelist:
            actual = hashlib.sha256(zf.read(p)).hexdigest()
        elif inner_zf and p in inner_namelist:
            actual = hashlib.sha256(inner_zf.read(p)).hexdigest()
        
        if actual is None:
            if p.endswith(".zip") or "MANIFEST" in p or "LEDGER" in p:
                fail(f"Critical manifest entry missing: {p}", acc, "FID-003", "Manifest Integrity")
                m_ok = False
            continue

        if actual != expected:
            fail(f"Hash mismatch for {p}", acc, "FID-003", "Manifest Integrity")
            m_ok = False
    return m_ok


def _seek_identity_in_drop(zf: zipfile.ZipFile, acc: GateAccumulator) -> Optional[Path]:
    """Search for sovereign.pub inside the drop or evidence zip."""
    namelist = zf.namelist()
    pub_key_bytes = None

    try:
        if "sovereign.pub" in namelist:
            pub_key_bytes = zf.read("sovereign.pub")
            print("  [+] Found identity in drop root.")
        else:
            evidence_names = [n for n in namelist if "TRADER_OPS_EVIDENCE" in n and n.endswith(".zip")]
            if evidence_names:
                e_bytes = zf.read(evidence_names[0])
                with zipfile.ZipFile(io.BytesIO(e_bytes)) as ez:
                    if "sovereign.pub" in ez.namelist():
                        pub_key_bytes = ez.read("sovereign.pub")
                        print(f"  [+] Found identity in {evidence_names[0]}.")
        
        if pub_key_bytes:
            temp_key = Path(tempfile.gettempdir()) / "sovereign_extracted.pub"
            temp_key.write_bytes(pub_key_bytes)
            return temp_key
    except Exception as e:
        warn(f"Identity Auto-Seek Encountered Error: {e}", acc, "FID-001", "Identity Verification")
    
    return None


def _verify_bindings(cert: dict, zf: zipfile.ZipFile, acc: GateAccumulator):
    """Verify certificate hash bindings to main manifest and data."""
    bindings = cert.get("bindings", {})
    namelist = zf.namelist()
    
    if "MANIFEST.json" in namelist:
        m_bytes = zf.read("MANIFEST.json")
        m_hash = hashlib.sha256(m_bytes).hexdigest()
        
        # Dual-Hash Schema (v4.5.72+)
        final_hash = bindings.get("manifest_sha256")
        payload_hash = bindings.get("payload_manifest_sha256")
        
        # Output both if present
        if payload_hash:
            print(f"  [+] payload_manifest_sha256 (Canon): {payload_hash[:12]}")
        if final_hash:
            print(f"  [+] manifest_sha256 (Final): {final_hash[:12]}")

        if final_hash == m_hash:
            ok("Certificate binds correctly to Final Manifest", acc, "INT-003", "Manifest Binding")
        elif payload_hash == m_hash:
            ok("Certificate binds correctly to Payload Manifest", acc, "INT-003", "Manifest Binding")
        else:
            fail(f"Certificate manifest binding mismatch: Expected {final_hash[:8] if final_hash else 'NONE'}, got {m_hash[:8]}", acc, "INT-003", "Manifest Binding")
    
    d_hash = bindings.get("data_hash")
    if d_hash and d_hash != "N/A" and len(d_hash) == 64:  # noqa: PLR2004
        ok(f"Data Provenance bound: {d_hash[:8]}", acc, "INT-005", "Data Hash Non-Empty")
    else:
        fail(f"Data hash invalid or empty: {d_hash}", acc, "INT-005", "Data Hash Non-Empty")


def _check_timeline_sovereignty(drop_path: Path, acc: GateAccumulator):
    """Verify sidecar filename binding to prevent timeline bait-and-switch."""
    drop_dir = drop_path.parent
    m = re.search(r"v(\d+\.\d+\.\d+)", drop_path.name)
    ver = m.group(1) if m else None
    
    sidecar = None
    if ver:
        c1 = drop_dir / f"DROP_PACKET_SHA256_v{ver}.txt"
        if c1.exists():
            sidecar = c1
            
    if not sidecar:
        sidecar = drop_dir / (drop_path.name + ".sha256")
        if not sidecar.exists():
             sidecar = drop_dir / "DROP_PACKET_SHA256.txt"
             if not sidecar.exists():
                 sidecar = None

    if not sidecar:
        fail("No timeline sidecar found (DROP_PACKET_SHA256_v*.txt).", acc, "TIM-001", "Timeline Sovereignty")
        return

    try:
        raw = sidecar.read_text().strip().split()
        if not raw:
             fail("Sidecar is empty", acc, "TIM-001", "Timeline Sovereignty")
             return
             
        sidecar_sha = raw[0].lower()
        sidecar_name = raw[1] if len(raw) >= 2 else None
        
        # Hash match
        actual_sha = hashlib.sha256(drop_path.read_bytes()).hexdigest()
        if sidecar_sha != actual_sha:
            fail(f"Sidecar hash mismatch: {sidecar_sha[:8]} != {actual_sha[:8]}", acc, "TIM-001", "Timeline Sovereignty")
        # Filename binding (Anti-Bait)
        elif not sidecar_name:
             fail("Sidecar missing filename binding", acc, "TIM-001", "Timeline Sovereignty")
        elif Path(sidecar_name).name != drop_path.name:
             fail(f"Sidecar binding mismatch: {sidecar_name} != {drop_path.name}", acc, "TIM-001", "Timeline Sovereignty")
        else:
             ok("Timeline sidecar verified and bound", acc, "TIM-001", "Timeline Sovereignty")
    except Exception as e:
        fail(f"Timeline verification error: {e}", acc, "TIM-001", "Timeline Sovereignty")


def audit_drop(drop_path: Path, pub_key_path: Path, strict: bool = False) -> bool:  # noqa: PLR0915, PLR0912
    acc = GateAccumulator()
    print(f"\n🦅 AUDITING DROP: {drop_path.name}")
    print("=" * 60)

    m = re.search(r"_v([\d\.]+)\.zip", drop_path.name)
    ARCHIVE_VERSION = m.group(1) if m else "UNKNOWN"

    if not drop_path.exists():
        fail(f"Drop packet missing: {drop_path}", acc, "FID-003", "Manifest Integrity")
        return False

    if pub_key_path.exists():
        # Verifying pubkey pin (P0-C)
        h = hashlib.sha256()
        h.update(pub_key_path.read_bytes())
        actual_pub_sha = h.hexdigest()
        if actual_pub_sha != TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256:
            fail(f"Sovereign identity hash mismatch! Expected {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256[:8]}, got {actual_pub_sha[:8]}", acc, "FID-001", "Sovereign Identity")
            if strict:
                return False
        else:
            ok(f"Sovereign identity verified (Pinned: {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256[:8]})", acc, "FID-001", "Sovereign Identity")
    elif strict:
        fail("Sovereign identity missing in strict mode.", acc, "FID-001", "Sovereign Identity")
        return False
    else:
        warn("Public key missing. Signature verification skipped.", acc, "FID-001", "Sovereign Identity")

    if strict:
        _check_timeline_sovereignty(drop_path, acc)

    try:
        with zipfile.ZipFile(drop_path, "r") as zf:
            namelist = zf.namelist()

            # 1. Manifest Phase
            if "MANIFEST.json" in namelist:
                m_bytes = zf.read("MANIFEST.json")
                manifest_data = json.loads(m_bytes)
                acc.version = ARCHIVE_VERSION
                
                inner_zf = None
                code_zips = [n for n in namelist if "TRADER_OPS_CODE" in n and n.endswith(".zip")]
                if code_zips:
                    try:
                        inner_zf = zipfile.ZipFile(io.BytesIO(zf.read(code_zips[0])))
                    except Exception:
                        inner_zf = None

                if _scan_manifest(zf, manifest_data, inner_zf, acc):
                    ok(f"Manifest verified ({len(manifest_data.get('file_sha256', {}))} entries)", acc, "FID-003", "Manifest Integrity")
                if inner_zf:
                    inner_zf.close()
            else:
                fail("MANIFEST.json missing from drop", acc, "FID-003", "Manifest Integrity")

            # 2. Identity Phase (Auto-Seek)
            if not pub_key_path.exists():
                print("🔍 Searching for Sovereign Identity inside drop...")
                found_key = _seek_identity_in_drop(zf, acc)
                if found_key:
                    pub_key_path = found_key
                    ok(f"Sovereign identity auto-detected: {pub_key_path.name}", acc, "FID-001", "Sovereign Identity")
                else:
                    fail("Sovereign Identity (sovereign.pub) missing.", acc, "FID-005", "Identity Verification")

            # 3. Certificate Phase
            evidence_zips = [n for n in namelist if "TRADER_OPS_EVIDENCE" in n and n.endswith(".zip")]
            cert_found = False
            if evidence_zips:
                ev_data = zf.read(evidence_zips[0])
                with zipfile.ZipFile(io.BytesIO(ev_data)) as evzf:
                    ev_namelist = evzf.namelist()
                    cert_path = "reports/certification/CERTIFICATE.json"
                    sig_path = "reports/certification/CERTIFICATE.json.sig"
                    
                    if cert_path in ev_namelist:
                        cert_found = True
                        cert_content = evzf.read(cert_path)
                        cert = json.loads(cert_content)
                        cert_ver = cert.get("version", "UNKNOWN")
                        acc.version = cert_ver 
                        
                        if cert_ver == ARCHIVE_VERSION:
                            ok(f"Certificate version matches: v{cert_ver}", acc, "FID-002A", "Certificate Version")
                        else:
                            fail(f"Certificate version mismatch: Cert({cert_ver}) != Filename({ARCHIVE_VERSION})", acc, "FID-002A", "Certificate Version")

                        if pub_key_path.exists() and sig_path in ev_namelist:
                            if verify_signature(cert_content, evzf.read(sig_path), pub_key_path):
                                ok("Sovereign Signature Verified (Ed25519)", acc, "FID-002B", "Certificate Signature")
                            else:
                                fail("Sovereign Signature INVALID", acc, "FID-002B", "Certificate Signature")
                        
                        _verify_bindings(cert, zf, acc)
            
            if not cert_found:
                fail("CERTIFICATE.json missing", acc, "FID-002C", "Certificate Presence")
            elif evidence_zips:
                ev_data = zf.read(evidence_zips[0])
                with zipfile.ZipFile(io.BytesIO(ev_data)) as evzf:
                    ev_namelist = evzf.namelist()
                    # EVID-001: EVIDENCE_SUITE_REQUIRED_FILES_PRESENT
                    req_evidence_files = [
                        "reports/forge/synthetic_smoke/RUN_METADATA.json",
                        "reports/forge/synthetic_smoke/EVIDENCE_MANIFEST.json",
                        "reports/forge/synthetic_smoke/DATA_MANIFEST.json",
                        "reports/forge/synthetic_smoke/results.csv",
                        "reports/certification/CERTIFICATE.json",
                        "reports/certification/CERTIFICATE.json.sig",
                        "reports/certification/sovereign.pub"
                    ]
                    missing_evid = [f for f in req_evidence_files if f not in ev_namelist]
                    if missing_evid:
                        fail(f"Missing evidence suite files: {missing_evid}", acc, "EVID-001", "Evidence Suite Complete")
                    else:
                        ok("Evidence suite required files are present", acc, "EVID-001", "Evidence Suite Complete")

                    # EVID-002: EVIDENCE_MANIFEST_ENUMERATION_COMPLETE
                    if "reports/forge/synthetic_smoke/EVIDENCE_MANIFEST.json" in ev_namelist:
                        em_raw = evzf.read("reports/forge/synthetic_smoke/EVIDENCE_MANIFEST.json")
                        try:
                            em = json.loads(em_raw)
                            files_dict = em.get("files", em.get("checksums", em.get("evidence", {})))
                            man_req = ["RUN_METADATA.json", "DATA_MANIFEST.json", "results.csv"]
                            if "reports/forge/synthetic_smoke/PROMPT_FINGERPRINT.json" in ev_namelist:
                                man_req.append("PROMPT_FINGERPRINT.json")
                            missing_man = [m for m in man_req if m not in files_dict]
                            if missing_man:
                                fail(f"Evidence manifest missing entries: {missing_man}", acc, "EVID-002", "Evidence Manifest Enumeration")
                            else:
                                ok("Evidence manifest enumeration complete", acc, "EVID-002", "Evidence Manifest Enumeration")
                        except Exception as e:
                            fail(f"Could not parse EVIDENCE_MANIFEST.json: {e}", acc, "EVID-002", "Evidence Manifest Enumeration")

                    # FID-006: PROMPT_FINGERPRINT_PRESENT_AND_VALID
                    pf_path = "reports/forge/synthetic_smoke/PROMPT_FINGERPRINT.json"
                    pf_sig_path = "reports/forge/synthetic_smoke/PROMPT_FINGERPRINT.json.sig"
                    if pf_path in ev_namelist:
                        try:
                            pf = json.loads(evzf.read(pf_path))
                            p_id = pf.get("prompt_id", "")
                            p_sha = pf.get("prompt_sha256", "")
                            if not p_id or not isinstance(p_id, str):
                                fail("PROMPT_FINGERPRINT.json missing valid prompt_id", acc, "FID-006", "Prompt Fingerprint Valid")
                            elif not p_sha or not re.fullmatch(r"[0-9a-fA-F]{64}", p_sha):
                                fail("PROMPT_FINGERPRINT.json missing valid prompt_sha256", acc, "FID-006", "Prompt Fingerprint Valid")
                            else:
                                if pf_sig_path in ev_namelist and pub_key_path.exists():
                                    pf_content = evzf.read(pf_path)
                                    pf_sig_content = evzf.read(pf_sig_path)
                                    if verify_signature(pf_content, pf_sig_content, pub_key_path):
                                        ok("Prompt Fingerprint Valid and Signature Verified", acc, "FID-006", "Prompt Fingerprint Valid")
                                    else:
                                        fail("PROMPT_FINGERPRINT.json.sig INVALID signature", acc, "FID-006", "Prompt Fingerprint Valid")
                                else:
                                    ok("Prompt Fingerprint format valid (no signature checked)", acc, "FID-006", "Prompt Fingerprint Valid")
                        except Exception as e:
                            fail(f"Failed to parse PROMPT_FINGERPRINT.json: {e}", acc, "FID-006", "Prompt Fingerprint Valid")
                    else:
                        fail("PROMPT_FINGERPRINT.json missing", acc, "FID-006", "Prompt Fingerprint Valid")

                    # INT-006: DATA_LEAF_HASH_BINDING
                    dm_path = "reports/forge/synthetic_smoke/DATA_MANIFEST.json"
                    if dm_path in ev_namelist and code_zips:
                        try:
                            dm = json.loads(evzf.read(dm_path))
                            file_sha_map = dm.get("file_sha256", {})
                            leaf_ok = True
                            with zipfile.ZipFile(io.BytesIO(zf.read(code_zips[0]))) as czf:
                                c_names = czf.namelist()
                                for fname, expected_sha in file_sha_map.items():
                                    data_p = f"data/{fname}"
                                    if data_p in c_names:
                                        actual_sha = hashlib.sha256(czf.read(data_p)).hexdigest()
                                        if actual_sha != expected_sha:
                                            fail(f"Data leaf hash mismatch for {fname}", acc, "INT-006", "Data Leaf Hash Binding")
                                            leaf_ok = False
                                    else:
                                        fail(f"Data leaf missing from CODE zip: {data_p}", acc, "INT-006", "Data Leaf Hash Binding")
                                        leaf_ok = False
                            if leaf_ok:
                                ok("All data leaves bound securely to code zip", acc, "INT-006", "Data Leaf Hash Binding")
                        except Exception as e:
                            fail(f"INT-006 verification failed: {e}", acc, "INT-006", "Data Leaf Hash Binding")
                    elif dm_path not in ev_namelist:
                        fail("DATA_MANIFEST.json missing for INT-006", acc, "INT-006", "Data Leaf Hash Binding")

            # 4. Seed Profile check
            if code_zips:
                try:
                    with zipfile.ZipFile(io.BytesIO(zf.read(code_zips[0]))) as czf:
                        if "profiles/seed_profile.yaml" in czf.namelist():
                            prof_txt = czf.read("profiles/seed_profile.yaml").decode("utf-8")
                            prof_txt_lower = prof_txt.lower()
                            if "live_trading_enabled: false" not in prof_txt_lower:
                                fail("seed_profile.yaml live_trading_enabled must be false", acc, "PROF-001", "Seed Profile Present and Safe")
                            elif "max_contracts" not in prof_txt and "max_position_size_contracts" not in prof_txt:
                                fail("seed_profile.yaml missing max_contracts", acc, "PROF-001", "Seed Profile Present and Safe")
                            elif "daily_loss_cap_usd" not in prof_txt:
                                fail("seed_profile.yaml missing daily_loss_cap_usd", acc, "PROF-001", "Seed Profile Present and Safe")
                            else:
                                ok("Seed Profile verified and safe", acc, "PROF-001", "Seed Profile Present and Safe")
                        else:
                            fail("profiles/seed_profile.yaml MISSING", acc, "PROF-001", "Seed Profile Present and Safe")
                except Exception as e:
                    fail(f"Failed to read CODE zip: {e}", acc, "PROF-001", "Seed Profile Present and Safe")

    except zipfile.BadZipFile:
        fail("Corrupt drop packet", acc, "FID-003", "Manifest Integrity")

    acc.emit_json(Path("dist/audit/gate_report.json"))
    has_fail = any(r.status == "FAIL" for r in acc.results)
    if has_fail:
        print(f"\n🛑 {RED}{BOLD}DROP REJECTED: One or more gates failed.{RESET}")
        return False

    print(f"\n🏆 {GREEN}{BOLD}DROP PASSED AUDIT.{RESET}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("drop_packet", type=Path)
    parser.add_argument("--pubkey", "--trusted-pubkey", dest="pubkey", type=Path, default=Path("keys/sovereign.pub"))
    parser.add_argument("--strict", action="store_true", help="Enable strict fiduciary audit")
    args = parser.parse_args()

    # Fallback to local sovereign.pub if keys/sovereign.pub missing and not in keys/ already
    if not args.pubkey.exists() and Path("sovereign.pub").exists():
        args.pubkey = Path("sovereign.pub")

    success = audit_drop(args.drop_packet, args.pubkey, args.strict)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
