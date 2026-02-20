#!/usr/bin/env python3
"""
scripts/verify_run_ledger_signature.py
======================================
v4.5.109 - Fiduciary Run Ledger Signature Verifier.
Validates the Ed25519 signature of the outer RUN_LEDGER.json.
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

# sys.path hacking to allow importing antigravity_harness from repo root
REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from antigravity_harness.trust_root import TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256 # noqa: E402

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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-ledger", required=True, help="Path to RUN_LEDGER_vX.Y.Z.json")
    ap.add_argument("--sig", help="Path to signature file (defaults to --run-ledger + .sig)")
    ap.add_argument("--trusted-pubkey", default="keys/sovereign.pub", help="Path to trusted public key")
    ap.add_argument("--strict", action="store_true", help="Enable strict mode requirements")
    args = ap.parse_args()

    ledger_path = Path(args.run_ledger)
    sig_path = Path(args.sig) if args.sig else Path(str(ledger_path) + ".sig")
    pub_path = Path(args.trusted_pubkey)

    print(f"🛡️  Verifying Run Ledger Signature: {ledger_path.name}")

    if not ledger_path.exists():
        print(f"❌ FAIL: Ledger file not found: {ledger_path}")
        sys.exit(2)
    if not sig_path.exists():
        print(f"❌ FAIL: Signature file not found: {sig_path}")
        sys.exit(2)
    if not pub_path.exists():
        print(f"❌ FAIL: Trusted public key missing: {pub_path}")
        sys.exit(2)

    # 1. Pubkey Pin Verification
    actual_pub_sha = sha256_file(pub_path)
    if actual_pub_sha != TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256:
        print("❌ FAIL: Trusted public key hash mismatch!")
        print(f"   Expected: {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256}")
        print(f"   Actual:   {actual_pub_sha}")
        sys.exit(2)
    print(f"✅ Trusted Public Key Verified (Pinned: {TRUST_ROOT_SOVEREIGN_PUBKEY_SHA256[:8]})")

    # 2. Signature Verification
    try:
        _openssl_verify_ed25519(pub_path, ledger_path, sig_path)
        print("✅ Run Ledger Signature Verified (Ed25519)")
    except Exception as e:
        print(f"❌ FAIL: Run Ledger Signature INVALID: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
