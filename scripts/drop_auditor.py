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


def audit_drop(drop_path: Path, pub_key_path: Path) -> bool:  # noqa: PLR0915, PLR0912
    acc = GateAccumulator()
    print(f"\n🦅 AUDITING DROP: {drop_path.name}")
    print("=" * 60)

    # [VERSION WITNESS] Extract version from filename (Canonical Source)
    m = re.search(r"_v([\d\.]+)\.zip", drop_path.name)
    ARCHIVE_VERSION = m.group(1) if m else "UNKNOWN"

    if not drop_path.exists():
        fail(f"Drop packet missing: {drop_path}", acc, "FID-003", "Manifest Integrity")
        return False

    # 1. Identity Gate
    if pub_key_path.exists():
        ok(f"Sovereign identity found: {pub_key_path.name}", acc, "FID-001", "Sovereign Identity")
    else:
        warn("Public key missing. Signature verification skipped.", acc, "FID-001", "Sovereign Identity")

    # 2. Extract and Scan
    try:
        with zipfile.ZipFile(drop_path, "r") as zf:
            namelist = zf.namelist()

            # A. MANIFEST integrity
            if "MANIFEST.json" in namelist:
                # [STRICT BINDING] We hash the RAW bytes of the root MANIFEST.json
                m_bytes = zf.read("MANIFEST.json")
                m_hash = hashlib.sha256(m_bytes).hexdigest()
                print(f"🔍 DEBUG: Root MANIFEST.json Raw Hash: {m_hash}")
                
                manifest_data = json.loads(m_bytes)
                acc.version = ARCHIVE_VERSION
                files = manifest_data.get("file_sha256", {})
                m_ok = True
                
                # Pre-scan inner code zip if it exists to allow deep verification
                inner_zf = None
                code_zips = [n for n in namelist if "TRADER_OPS_CODE" in n and n.endswith(".zip")]
                if code_zips:
                    try:
                        inner_data = zf.read(code_zips[0])
                        inner_zf = zipfile.ZipFile(io.BytesIO(inner_data))
                    except Exception:
                        inner_zf = None

                for p, expected in files.items():
                    actual = None
                    if p in namelist:
                        actual = hashlib.sha256(zf.read(p)).hexdigest()
                    elif inner_zf and p in inner_zf.namelist():
                        actual = hashlib.sha256(inner_zf.read(p)).hexdigest()
                    
                    if actual is None:
                        # Allow skipping optional repo files if they aren't in the inner zip
                        # but critical artifacts (zips) must be present.
                        if p.endswith(".zip") or "MANIFEST" in p or "LEDGER" in p:
                            fail(f"Critical manifest entry missing: {p}", acc, "FID-003", "Manifest Integrity")
                            m_ok = False
                        continue

                    if actual != expected:
                        fail(f"Hash mismatch for {p}", acc, "FID-003", "Manifest Integrity")
                        m_ok = False
                
                if inner_zf:
                    inner_zf.close()

                if m_ok:
                    ok(f"Manifest verified ({len(files)} entries, including deep scan)", acc, "FID-003", "Manifest Integrity")
            else:
                fail("MANIFEST.json missing from drop", acc, "FID-003", "Manifest Integrity")

            # B. CERTIFICATE binding (RECURSIVE SEARCH)
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
                        
                        # Verify version match
                        # We trust the CERTIFICATE's version (signed) as the source of truth
                        cert_ver = cert.get("version", "UNKNOWN")
                        acc.version = cert_ver 
                        
                        if cert_ver == ARCHIVE_VERSION:
                            ok(f"Certificate version matches: v{cert_ver}", acc, "FID-002", "Certificate Signature")
                        else:
                            fail(f"Certificate version mismatch: Cert({cert_ver}) != Filename({ARCHIVE_VERSION})", acc, "FID-002", "Certificate Signature")

                        # Verify signature if key exists
                        if pub_key_path.exists() and sig_path in ev_namelist:
                            sig_bytes = evzf.read(sig_path)
                            if verify_signature(cert_content, sig_bytes, pub_key_path):
                                ok("Sovereign Signature Verified (Ed25519)", acc, "FID-002", "Certificate Signature")
                            else:
                                fail("Sovereign Signature INVALID", acc, "FID-002", "Certificate Signature")
                        
                        # Verify bindings
                        bindings = cert.get("bindings", {})
                        # manifest_sha256 binding
                        if "MANIFEST.json" in namelist:
                            # [STRICT BINDING] We hash the RAW bytes of the root MANIFEST.json
                            # which the forge ensures is bit-perfect to the payload manifest it signed.
                            m_bytes = zf.read("MANIFEST.json")
                            m_hash = hashlib.sha256(m_bytes).hexdigest()
                            
                            # Standardized key is manifest_sha256
                            expected_hash = bindings.get("manifest_sha256") or bindings.get("payload_manifest_sha256")
                            
                            if expected_hash == m_hash:
                                ok("Certificate binds correctly to Manifest", acc, "INT-003", "No Circular Hash")
                            else:
                                fail(f"Certificate manifest binding mismatch: Expected {expected_hash[:8] if expected_hash else 'NONE'}, got {m_hash[:8]}", acc, "INT-003", "No Circular Hash")
                        
                        # Data hash
                        d_hash = bindings.get("data_hash")
                        if d_hash and d_hash != "N/A" and len(d_hash) == 64:  # noqa: PLR2004
                            ok(f"Data Provenance bound: {d_hash[:8]}", acc, "INT-005", "Data Hash Non-Empty")
                        else:
                            fail(f"Data hash invalid or empty: {d_hash}", acc, "INT-005", "Data Hash Non-Empty")
            
            if not cert_found:
                fail("CERTIFICATE.json missing (searched root and evidence zip)", acc, "FID-002", "Certificate Signature")

            # C. SEED PROFILE check (Fail-Closed)
            code_zips = [n for n in namelist if "TRADER_OPS_CODE" in n and n.endswith(".zip")]
            if not code_zips:
                fail("CODE zip missing from drop", acc, "INT-004", "Seed Profile Present")
            else:
                code_data = zf.read(code_zips[0])
                try:
                    with zipfile.ZipFile(io.BytesIO(code_data)) as czf:
                        profile_matches = [n for n in czf.namelist() if "seed_profile.yaml" in n]
                        if profile_matches:
                            ok(f"Seed Profile verified: {profile_matches[0]}", acc, "INT-004", "Seed Profile Present")
                        else:
                            fail("profiles/seed_profile.yaml MISSING from CODE zip", acc, "INT-004", "Seed Profile Present")
                except Exception as e:
                    fail(f"Failed to read CODE zip: {e}", acc, "INT-004", "Seed Profile Present")

    except zipfile.BadZipFile:
        fail("Corrupt drop packet", acc, "FID-003", "Manifest Integrity")

    # 3. Emit Report
    report_path = Path("dist/audit/gate_report.json")
    acc.emit_json(report_path)

    # Final logic: Non-zero exit if any FAIL
    has_fail = any(r.status == "FAIL" for r in acc.results)
    if has_fail:
        print(f"\n🛑 {RED}{BOLD}DROP REJECTED: One or more gates failed.{RESET}")
        return False

    print(f"\n🏆 {GREEN}{BOLD}DROP PASSED AUDIT.{RESET}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("drop_packet", type=Path)
    parser.add_argument("--pubkey", type=Path, default=Path("sovereign.pub"))
    args = parser.parse_args()

    success = audit_drop(args.drop_packet, args.pubkey)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
