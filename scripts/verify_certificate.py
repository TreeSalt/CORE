#!/usr/bin/env python3
"""
verify_certificate.py — Standalone Fiduciary Certificate Verifier.
Validates Ed25519 signature against evidence contents.
Exit codes: 0 = PASS, 2 = FAIL.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# sys.path hacking to allow importing antigravity_harness from repo root
REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from antigravity_harness.trust_root import TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256  # noqa: E402


def _openssl_verify_ed25519(pub_pem: Path, msg: Path, sig: Path) -> None:
    """Verify Ed25519 signature using OpenSSL."""
    cmd = [
        "openssl", "pkeyutl", "-verify", "-rawin",
        "-pubin", "-inkey", str(pub_pem),
        "-in", str(msg),
        "-sigfile", str(sig),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"Signature verify failed: {err}")

def main():  # noqa: PLR0912, PLR0915
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True, help="Path to TRADER_OPS_EVIDENCE_v*.zip")
    ap.add_argument("--trusted-pubkey", default="keys/sovereign.pub", help="Path to out-of-band trusted Sovereign public key")
    ap.add_argument("--strict", action="store_true", help="Enable strict fiduciary check")
    args = ap.parse_args()

    print(f"📜 Verifying Certificate in: {args.evidence}")
    
    if not os.path.exists(args.evidence):
        print(f"❌ FAIL: Evidence zip not found: {args.evidence}")
        sys.exit(2)

    # --- Trust Root Verification (P0-C)
    trusted_pub_path = Path(args.trusted_pubkey)
    if not trusted_pub_path.exists():
        if args.strict:
            print(f"❌ FAIL: Trusted public key missing at {args.trusted_pubkey}")
            sys.exit(2)
        else:
            print(f"⚠️  WARN: Trusted public key missing at {args.trusted_pubkey}. Falling back to artifact key.")
    else:
        # Verify hash pinning
        h = hashlib.sha256()
        with open(trusted_pub_path, "rb") as f:
             for chunk in iter(lambda: f.read(4096), b""):
                 h.update(chunk)
        actual_pub_sha = h.hexdigest()
        if actual_pub_sha != TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256:
            print("❌ FAIL: Trusted public key hash mismatch!")
            print(f"   Expected: {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256}")
            print(f"   Actual:   {actual_pub_sha}")
            sys.exit(2)
        print(f"✅ Trusted Public Key Verified (Pinned: {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256[:8]})")

    try:
        with zipfile.ZipFile(args.evidence, 'r') as zf:
            names = set(zf.namelist())
            
            cert_path = "reports/certification/CERTIFICATE.json"
            sig_path = "reports/certification/CERTIFICATE.json.sig"
            pub_path = "reports/certification/sovereign.pub"

            for p in [cert_path, sig_path, pub_path]:
                if p not in names:
                    print(f"❌ FAIL: {p} missing from evidence")
                    sys.exit(2)

            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                p_cert = tmp / "CERTIFICATE.json"
                p_sig = tmp / "CERTIFICATE.json.sig"
                p_pub = tmp / "sovereign.pub"

                p_cert.write_bytes(zf.read(cert_path))
                p_sig.write_bytes(zf.read(sig_path))
                
                if trusted_pub_path.exists():
                    p_pub.write_bytes(trusted_pub_path.read_bytes())
                else:
                    p_pub.write_bytes(zf.read(pub_path))

                # Coherence Check: strict_mode must be true
                cert_data = json.loads(p_cert.read_text())
                if cert_data.get("strict_mode") is not True:
                    print("❌ FAIL: Certificate strict_mode is not true")
                    sys.exit(2)

                _openssl_verify_ed25519(p_pub, p_cert, p_sig)
                
                print(f"✅ Certificate Verified. Version: {cert_data.get('trader_ops_version')}")
                print(f"   Git Commit: {cert_data.get('git_commit')} (Dirty: {cert_data.get('git_dirty')})")

    except Exception as e:
        print(f"❌ FAIL: Verification error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
