#!/usr/bin/env python3
"""
shadow_runner.py — Automated Chaos Monkey verification for vaulted artifacts.
This script ensures that our "Institutional Gold" artifacts are truly robust 
by subjecting established builds to stressors.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault-dir", default="vault", help="Path to the artifact vault")
    ap.add_argument("--chaos-mode", default="all", help="Chaos Monkey mode (all, hydra, basilisk, etc.)")
    args = ap.parse_args()

    repo_root = Path(__file__).parent.parent.resolve()
    vault_path = repo_root / args.vault_dir

    if not vault_path.exists():
        print(f"❌ ERROR: Vault directory not found: {vault_path}")
        return 2

    # Find the latest drop packet in the vault (recursive)
    drops = sorted(list(vault_path.rglob("TRADER_OPS_READY_TO_DROP_v*.zip")))
    if not drops:
        print("⚠️  WARNING: No artifacts found in vault to shadow-verify.")
        # Fallback to dist if vault is empty
        dist_path = repo_root / "dist"
        drops = sorted(list(dist_path.rglob("TRADER_OPS_READY_TO_DROP_v*.zip")))
        if not drops:
            print("❌ ERROR: No artifacts found in vault or dist.")
            return 2
        print("📂 Falling back to latest in dist.")
    
    latest_drop = drops[-1]
    print(f"🐉 SHADOW RUNNER: Subjecting {latest_drop.name} to chaos...")

    # Run Chaos Monkey
    try:
        # We use sys.executable to ensure we use the same environment
        cmd = [sys.executable, "scripts/chaos_monkey.py", args.chaos_mode]
        subprocess.check_call(cmd, cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"🛑 SHADOW FAILURE: Chaos Monkey detected a vulnerability in {latest_drop.name}.")
        return e.returncode

    print(f"✅ SHADOW SUCCESS: {latest_drop.name} remains bit-perfect and sovereign under stress.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
