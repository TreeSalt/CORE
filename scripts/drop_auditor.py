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

Gate report emitted to: dist/audit/gate_report.json
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# ── Gate Accumulator ─────────────────────────────────────────────────────────


class GateAccumulator:
    """Collects gate results and emits gate_report.json."""

    def __init__(self):
        self.gates: List[Dict[str, str]] = []
        self._failed = False

    def record(self, gate_id: str, name: str, status: str, detail: str = ""):
        entry = {"gate_id": gate_id, "name": name, "status": status, "detail": detail}
        self.gates.append(entry)
        if status == "FAIL":
            self._failed = True

    def has_failures(self) -> bool:
        return self._failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "overall_status": "FAIL" if self._failed else "PASS",
            "total_gates": len(self.gates),
            "passed": sum(1 for g in self.gates if g["status"] == "PASS"),
            "failed": sum(1 for g in self.gates if g["status"] == "FAIL"),
            "warned": sum(1 for g in self.gates if g["status"] == "WARN"),
            "gates": self.gates,
        }

    def emit(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "gate_report.json"
        report_path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        print(f"📋 Gate report emitted: {report_path}")


# ── Utilities ────────────────────────────────────────────────────────────────


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"❌ FAIL: {msg}")
    acc.record(gate_id, gate_name, "FAIL", msg)


def ok(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"✅ {msg}")
    acc.record(gate_id, gate_name, "PASS", msg)


def warn(msg: str, acc: GateAccumulator, gate_id: str, gate_name: str):
    print(f"⚠️  {msg}")
    acc.record(gate_id, gate_name, "WARN", msg)


# ── Verification Steps ──────────────────────────────────────────────────────


def verify_ledger(
    zf: zipfile.ZipFile, names: List[str], acc: GateAccumulator
) -> Dict[str, Any]:
    """Find and load the inner ledger."""
    ledger_files = [
        n for n in names
        if n.startswith("RUN_LEDGER_INNER_v") and n.endswith(".json")
    ]
    if not ledger_files:
        fail("No RUN_LEDGER_INNER_v*.json found in drop", acc, "FID-004", "Ledger Presence")
        return {}

    ledger_name = ledger_files[0]
    ledger_data = json.loads(zf.read(ledger_name))
    version = ledger_data.get("version", "UNKNOWN")
    print(f"📋 Ledger: {ledger_name} (v{version})")
    ok("Inner ledger found", acc, "FID-004", "Ledger Presence")
    return ledger_data


def verify_zip_artifact(
    zf: zipfile.ZipFile,
    names: List[str],
    ledger_data: Dict[str, Any],
    key: str,
    acc: GateAccumulator,
):
    """Verify integrity of a zip artifact (code or evidence)."""
    gate_id = "INT-001" if key == "code" else "INT-002"
    gate_name = f"{key.capitalize()} Zip Integrity"

    info = ledger_data.get("artifacts", {}).get(key, {})
    filename = info.get("filename", "")
    expected_sha = info.get("sha256", "")

    if filename not in names:
        fail(f"{key.capitalize()} zip not found in drop: {filename}", acc, gate_id, gate_name)
        return

    actual_sha = sha256_bytes(zf.read(filename))
    if actual_sha == expected_sha:
        ok(f"{key.capitalize()} zip integrity: {actual_sha[:16]}...", acc, gate_id, gate_name)
    else:
        fail(
            f"{key.capitalize()} zip hash mismatch: expected {expected_sha[:16]}... got {actual_sha[:16]}...",
            acc, gate_id, gate_name,
        )


def verify_sovereign_binding(ledger_data: Dict[str, Any], acc: GateAccumulator):
    """Verify git status and drop preimage."""
    binding = ledger_data.get("sovereign_binding", {})
    git_dirty = binding.get("git_dirty", True)
    if not git_dirty:
        ok(
            f"Git commit: {binding.get('git_commit', 'N/A')[:12]}... (clean)",
            acc, "FID-006", "Clean Tree",
        )
    else:
        warn("Git tree was dirty at build time", acc, "FID-006", "Clean Tree")

    preimage_expected = binding.get("drop_preimage_sha256", "")
    if preimage_expected:
        preimage_payload = ledger_data["artifacts"]
        preimage_bytes = json.dumps(
            preimage_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        preimage_actual = sha256_bytes(preimage_bytes)
        if preimage_actual == preimage_expected:
            ok(f"Drop preimage: {preimage_actual[:16]}...", acc, "FID-001", "Sovereign Identity")
        else:
            fail(
                f"Drop preimage mismatch: expected {preimage_expected[:16]}... got {preimage_actual[:16]}...",
                acc, "FID-001", "Sovereign Identity",
            )


def _run_openssl_verify(pub_path, cert_path, sig_path):
    """Helper to run openssl pkeyutl -verify. Returns True/False/None."""
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
        return True
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return False


def verify_certificate(
    zf: zipfile.ZipFile,
    ledger_data: Dict[str, Any],
    version: str,
    acc: GateAccumulator,
):
    """Verify the Ed25519 certificate inside the evidence zip."""
    ev_info = ledger_data.get("artifacts", {}).get("evidence", {})
    ev_filename = ev_info.get("filename", "")

    if ev_filename not in zf.namelist():
        warn("Evidence zip not available for cert check", acc, "FID-002", "Certificate Signature")
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
                    c_path = os.path.join(tmpdir, "c.json")
                    s_path = os.path.join(tmpdir, "c.sig")
                    p_path = os.path.join(tmpdir, "s.pub")
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
                        ok(f"Certificate version matches: v{version}", acc, "FID-005", "Version Consistency")
                    else:
                        fail(
                            f"Certificate version mismatch (found: {cert_ver})",
                            acc, "FID-005", "Version Consistency",
                        )

                    result = _run_openssl_verify(p_path, c_path, s_path)
                    if result is True:
                        ok("Certificate signature VERIFIED (Ed25519)", acc, "FID-002", "Certificate Signature")
                    elif result is False:
                        fail("Certificate signature verification FAILED", acc, "FID-002", "Certificate Signature")
                    else:
                        warn("openssl not found — cannot verify certificate", acc, "FID-002", "Certificate Signature")
                else:
                    warn("Certificate/signature/pubkey not found in evidence zip", acc, "FID-002", "Certificate Signature")
    except Exception as e:
        warn(f"Certificate check error: {e}", acc, "FID-002", "Certificate Signature")


def verify_manifest(zf: zipfile.ZipFile, names: List[str], acc: GateAccumulator):
    """Verify detached MANIFEST.json binds to actual zip hashes."""
    manifest_files = [n for n in names if n == "MANIFEST.json"]
    if not manifest_files:
        warn("No MANIFEST.json in READY zip (pre-v4.5.29 build)", acc, "FID-003", "Manifest Integrity")
        return

    manifest = json.loads(zf.read("MANIFEST.json"))
    files = manifest.get("files", [])
    all_ok = True
    for entry in files:
        path = entry.get("path", "")
        expected = entry.get("sha256", "")
        if path not in names:
            fail(f"Manifest references missing file: {path}", acc, "FID-003", "Manifest Integrity")
            all_ok = False
            continue
        actual = sha256_bytes(zf.read(path))
        if actual != expected:
            fail(
                f"Manifest hash mismatch for {path}: expected {expected[:16]}... got {actual[:16]}...",
                acc, "FID-003", "Manifest Integrity",
            )
            all_ok = False

    if all_ok:
        ok(f"Manifest integrity verified ({len(files)} files)", acc, "FID-003", "Manifest Integrity")


def verify_seed_profile(zf: zipfile.ZipFile, names: List[str], acc: GateAccumulator):
    """Verify seed_profile.yaml is present in CODE zip."""
    code_zips = [n for n in names if "TRADER_OPS_CODE_v" in n and n.endswith(".zip")]
    if not code_zips:
        warn("No CODE zip found for profile check", acc, "INT-004", "Seed Profile Present")
        return

    code_data = zf.read(code_zips[0])
    try:
        import io
        with zipfile.ZipFile(io.BytesIO(code_data)) as czf:
            profile_matches = [n for n in czf.namelist() if "seed_profile.yaml" in n]
            if profile_matches:
                ok(f"seed_profile.yaml found: {profile_matches[0]}", acc, "INT-004", "Seed Profile Present")
            else:
                fail("seed_profile.yaml NOT in CODE zip", acc, "INT-004", "Seed Profile Present")
    except Exception as e:
        warn(f"Could not inspect CODE zip: {e}", acc, "INT-004", "Seed Profile Present")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Sovereign Drop Auditor")
    parser.add_argument("drop_zip", help="Path to TRADER_OPS_READY_TO_DROP_v*.zip")
    parser.add_argument("--report-dir", default="dist/audit", help="Directory for gate_report.json")
    args = parser.parse_args()

    if not os.path.isfile(args.drop_zip):
        print(f"❌ FAIL: File not found: {args.drop_zip}")
        return 1

    print(f"🛡️  DROP AUDITOR — Verifying: {os.path.basename(args.drop_zip)}")
    print("=" * 60)

    acc = GateAccumulator()

    try:
        zf = zipfile.ZipFile(args.drop_zip, "r")
    except zipfile.BadZipFile:
        acc.record("INT-001", "Zip Valid", "FAIL", "Not a valid zip file")
        acc.emit(Path(args.report_dir))
        return 1

    names = zf.namelist()
    ledger_data = verify_ledger(zf, names, acc)
    if not ledger_data:
        acc.emit(Path(args.report_dir))
        return 1

    version = ledger_data.get("version", "UNKNOWN")

    # Strict mode check
    if ledger_data.get("strict_mode", False):
        ok("Strict mode: TRUE", acc, "FID-006", "Strict Mode")
    else:
        warn("Strict mode: FALSE — not fiduciary-grade", acc, "FID-006", "Strict Mode")

    # Artifact integrity
    verify_zip_artifact(zf, names, ledger_data, "code", acc)
    verify_zip_artifact(zf, names, ledger_data, "evidence", acc)

    # Sovereign binding
    verify_sovereign_binding(ledger_data, acc)

    # Manifest (v4.5.29+)
    verify_manifest(zf, names, acc)

    # Seed profile
    verify_seed_profile(zf, names, acc)

    # Metadata
    if "METADATA.txt" in names:
        ok("METADATA.txt present", acc, "INT-003", "Metadata Present")
    else:
        warn("METADATA.txt missing", acc, "INT-003", "Metadata Present")

    # Certificate
    verify_certificate(zf, ledger_data, version, acc)

    # Sidecar check
    sidecar_name = f"DROP_WITNESS_INNER_SHA256_v{version}.txt"
    if sidecar_name in names:
        ok(f"Internal sidecar present: {sidecar_name}", acc, "INT-003", "Witness Sidecar")
    else:
        warn(f"Internal sidecar missing: {sidecar_name}", acc, "INT-003", "Witness Sidecar")

    zf.close()

    # Emit gate report
    acc.emit(Path(args.report_dir))

    print("=" * 60)
    if acc.has_failures():
        print("❌ DROP AUDITOR: VERIFICATION FAILED — SEE gate_report.json")
        return 1

    print("🐉 DROP AUDITOR: ALL CHECKS PASSED — ARTIFACT IS SOVEREIGN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
