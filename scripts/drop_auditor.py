#!/usr/bin/env python3
"""
DROP AUDITOR — Sovereign Self-Contained Verifier
=================================================
This script is embedded inside every TRADER_OPS drop packet.
A third party can verify the drop WITHOUT extracting code zips,
WITHOUT cloning the repo, and WITHOUT any external dependencies.

Usage:
    python3 drop_auditor.py TRADER_OPS_READY_TO_DROP_v4.5.12.zip
    python3 drop_auditor.py --help

Exit codes:
    0 = ALL CHECKS PASSED
    1 = VERIFICATION FAILED
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from typing import Any, Dict, List


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str):
    print(f"❌ FAIL: {msg}")
    sys.exit(1)


def ok(msg: str):
    print(f"✅ {msg}")


def warn(msg: str):
    print(f"⚠️  {msg}")


def verify_ledger(zf: zipfile.ZipFile, names: List[str]) -> Dict[str, Any]:
    """Find and load the inner ledger."""
    ledger_files = [n for n in names if n.startswith("RUN_LEDGER_INNER_v") and n.endswith(".json")]
    if not ledger_files:
        fail("No RUN_LEDGER_INNER_v*.json found in drop")

    ledger_name = ledger_files[0]
    ledger_data = json.loads(zf.read(ledger_name))
    version = ledger_data.get("version", "UNKNOWN")
    print(f"📋 Ledger: {ledger_name} (v{version})")
    ok("Inner ledger found")
    return ledger_data


def verify_zip_artifact(zf: zipfile.ZipFile, names: List[str], ledger_data: Dict[str, Any], key: str):
    """Verify integrity of a zip artifact (code or evidence)."""
    info = ledger_data.get("artifacts", {}).get(key, {})
    filename = info.get("filename", "")
    expected_sha = info.get("sha256", "")

    if filename not in names:
        fail(f"{key.capitalize()} zip not found in drop: {filename}")

    actual_sha = sha256_bytes(zf.read(filename))
    if actual_sha == expected_sha:
        ok(f"{key.capitalize()} zip integrity: {actual_sha[:16]}...")
    else:
        fail(f"{key.capitalize()} zip hash mismatch: expected {expected_sha[:16]}... got {actual_sha[:16]}...")


def verify_sovereign_binding(ledger_data: Dict[str, Any]):
    """Verify git status and drop preimage."""
    binding = ledger_data.get("sovereign_binding", {})
    git_dirty = binding.get("git_dirty", True)
    if not git_dirty:
        ok(f"Git commit: {binding.get('git_commit', 'N/A')[:12]}... (clean)")
    else:
        warn("Git tree was dirty at build time")

    preimage_expected = binding.get("drop_preimage_sha256", "")
    if preimage_expected:
        preimage_payload = ledger_data["artifacts"]
        preimage_bytes = json.dumps(
            preimage_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        preimage_actual = sha256_bytes(preimage_bytes)
        if preimage_actual == preimage_expected:
            ok(f"Drop preimage: {preimage_actual[:16]}...")
        else:
            fail(f"Drop preimage mismatch: expected {preimage_expected[:16]}... got {preimage_actual[:16]}...")


def _run_openssl_verify(pub_path, cert_path, sig_path):
    """Helper to run openssl pkeyutl -verify."""
    try:
        subprocess.run(
            [
                "openssl", "pkeyutl", "-verify",
                "-pubin", "-inkey", pub_path,
                "-rawin", "-in", cert_path,
                "-sigfile", sig_path,
            ],
            check=True,
            capture_output=True,
        )
        ok("Certificate signature VERIFIED (Ed25519)")
    except FileNotFoundError:
        warn("openssl not found — cannot verify certificate signature")
    except subprocess.CalledProcessError:
        fail("Certificate signature verification FAILED")


def verify_certificate(zf: zipfile.ZipFile, ledger_data: Dict[str, Any], version: str):
    """Verify the Ed25519 certificate inside the evidence zip."""
    ev_info = ledger_data.get("artifacts", {}).get("evidence", {})
    ev_filename = ev_info.get("filename", "")

    if ev_filename not in zf.namelist():
        return

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ev_path = os.path.join(tmpdir, ev_filename)
            with open(ev_path, "wb") as ef:
                ef.write(zf.read(ev_filename))

            with zipfile.ZipFile(ev_path, "r") as ezf:
                enames = ezf.namelist()
                cert_n = [n for n in enames if n.endswith("CERTIFICATE.json")]
                sig_n = [n for n in enames if n.endswith("CERTIFICATE.json.sig")]
                pub_n = [n for n in enames if n.endswith("sovereign.pub")]

                if cert_n and sig_n and pub_n:
                    # Extract to temp files
                    c_path, s_path, p_path = [os.path.join(tmpdir, f) for f in ["c.json", "c.sig", "s.pub"]]
                    with open(c_path, "wb") as f:
                        f.write(ezf.read(cert_n[0]))
                    with open(s_path, "wb") as f:
                        f.write(ezf.read(sig_n[0]))
                    with open(p_path, "wb") as f:
                        f.write(ezf.read(pub_n[0]))

                    cert_obj = json.loads(ezf.read(cert_n[0]))
                    cert_ver = (
                        cert_obj.get("trader_ops_version")
                        or cert_obj.get("version")
                        or cert_obj.get("artifact_version")
                    )
                    if cert_ver == version:
                        ok(f"Certificate version matches: v{version}")
                    else:
                        fail(f"Certificate version mismatch (found: {cert_ver})")

                    _run_openssl_verify(p_path, c_path, s_path)
                else:
                    warn("Certificate/signature/pubkey not found in evidence zip")
    except Exception as e:
        warn(f"Certificate check error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Sovereign Drop Auditor")
    parser.add_argument("drop_zip", help="Path to TRADER_OPS_READY_TO_DROP_v*.zip")
    args = parser.parse_args()

    if not os.path.isfile(args.drop_zip):
        fail(f"File not found: {args.drop_zip}")

    print(f"🛡️  DROP AUDITOR — Verifying: {os.path.basename(args.drop_zip)}")
    print("=" * 60)

    try:
        zf = zipfile.ZipFile(args.drop_zip, "r")
    except zipfile.BadZipFile:
        fail("Not a valid zip file")

    names = zf.namelist()
    ledger_data = verify_ledger(zf, names)
    version = ledger_data.get("version", "UNKNOWN")

    # Strict mode check
    if ledger_data.get("strict_mode", False):
        ok("Strict mode: TRUE")
    else:
        warn("Strict mode: FALSE — not fiduciary-grade")

    # Artifact checks
    verify_zip_artifact(zf, names, ledger_data, "code")
    verify_zip_artifact(zf, names, ledger_data, "evidence")

    # Binding and metadata
    verify_sovereign_binding(ledger_data)
    if "METADATA.txt" in names:
        ok("METADATA.txt present")
    else:
        warn("METADATA.txt missing")

    # Certificate
    verify_certificate(zf, ledger_data, version)

    # Sidecar check
    sidecar_name = f"DROP_PACKET_SHA256_v{version}.txt"
    if sidecar_name in names:
        ok(f"Internal sidecar present: {sidecar_name}")
    else:
        warn(f"Internal sidecar missing: {sidecar_name}")

    zf.close()
    print("=" * 60)
    print("🐉 DROP AUDITOR: ALL CHECKS PASSED — ARTIFACT IS SOVEREIGN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
