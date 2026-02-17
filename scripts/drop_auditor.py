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
import logging
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GateResult:
    id: str
    name: str
    status: str  # PASS, FAIL, WARN
    message: str


@dataclass
class GateAccumulator:
    results: List[GateResult] = field(default_factory=list)

    def record(self, gate_id: str, name: str, status: str, message: str):
        self.results.append(GateResult(gate_id, name, status, message))

    def emit_json(self, path: Path):
        data = {
            "version": "4.5.29",
            "timestamp": datetime.utcnow().isoformat() + "Z",
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


def verify_signature(file_path: Path, sig_path: Path, pub_path: Path) -> Optional[bool]:
    """Verify DER signature using openssl."""
    if not sig_path.exists() or not pub_path.exists():
        return None
    try:
        subprocess.check_call(
            ["openssl", "dgst", "-sha256", "-verify", str(pub_path), "-signature", str(sig_path), str(file_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return False


def audit_drop(drop_path: Path, pub_key_path: Path) -> bool:  # noqa: PLR0915, PLR0912
    acc = GateAccumulator()
    print(f"\n🦅 AUDITING DROP: {drop_path.name}")
    print("=" * 60)

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
                manifest_data = json.loads(zf.read("MANIFEST.json"))
                files = manifest_data.get("files", [])
                m_ok = True
                for entry in files:
                    p = entry["path"]
                    expected = entry["sha256"]
                    if p not in namelist:
                        fail(f"Manifest entry missing from zip: {p}", acc, "FID-003", "Manifest Integrity")
                        m_ok = False
                        continue
                    actual = hashlib.sha256(zf.read(p)).hexdigest()
                    if actual != expected:
                        fail(f"Hash mismatch for {p}", acc, "FID-003", "Manifest Integrity")
                        m_ok = False
                if m_ok:
                    ok(f"Manifest verified ({len(files)} files)", acc, "FID-003", "Manifest Integrity")
            else:
                fail("MANIFEST.json missing from drop", acc, "FID-003", "Manifest Integrity")

            # B. CERTIFICATE binding
            if "CERTIFICATE.json" in namelist:
                cert = json.loads(zf.read("CERTIFICATE.json"))
                # Verify cert binds to manifest
                if "MANIFEST.json" in namelist:
                    m_hash = hashlib.sha256(zf.read("MANIFEST.json")).hexdigest()
                    if cert.get("manifest_hash") == m_hash:
                        ok("Certificate binds correctly to Manifest", acc, "INT-003", "No Circular Hash")
                    else:
                        fail("Certificate manifest_hash mismatch", acc, "INT-003", "No Circular Hash")
                
                # Verify data_hash
                d_hash = cert.get("bindings", {}).get("data_hash")
                if d_hash and d_hash != "N/A" and len(d_hash) == 64:  # noqa: PLR2004
                    ok(f"Data Provenance bound: {d_hash[:8]}", acc, "INT-005", "Data Hash Non-Empty")
                else:
                    fail(f"Data hash invalid or empty: {d_hash}", acc, "INT-005", "Data Hash Non-Empty")
            else:
                fail("CERTIFICATE.json missing", acc, "FID-002", "Certificate Signature")

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
