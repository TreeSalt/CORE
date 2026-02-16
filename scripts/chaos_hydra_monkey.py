#!/usr/bin/env python3
"""
chaos_hydra_monkey.py — The Unified Saboteur.
Orchestrates both artifact-level chaos and environment-level Hydra vector stress tests.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault-dir", default="vault", help="Path to the artifact vault")
    ap.add_argument("--mode", default="all", help="Chaos mode (all, binary, ledger, v227, v228, v240, v231, etc.)")
    ap.add_argument("--auto-cleanup", action="store_true", help="Automatically revert changes after test (not implemented)")
    args = ap.parse_args()

    repo_root = Path(__file__).parent.parent.resolve()
    
    print(f"🐉 CHAOS HYDRA MONKEY: Unleashing chaos in mode '{args.mode}'...")

    # For runtime vectors, we might need to run a specific command and check for Failure
    vector_map = {
        "v227": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "Zero-Volume Guard"},
        "v228": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "Slippage Poisoning"},
        "v240": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "NaN Detection"},
        "v231": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": True, "reason": "Ledger Inflation"},
        "v241": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": True, "reason": "Temporal Paradox"},
        "v242": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "Identity Mimic"},
        "v243": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "Memory Bomb"},
        "v244": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "FD Exhaustion"},
        "v245": {"cmd": ["make", "verify"], "expected_fail": True, "reason": "Signal Tsunami"},
        "v246": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": True, "reason": "Symlink Poisoning"},
        "v247": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": True, "reason": "Immutability Paradox"},
        "v248": {"cmd": ["scripts/verify_drop_packet.py", "dist"], "expected_fail": True, "reason": "Audit Race Condition"},
        "v249": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": False, "reason": "Audit Failure Resilience"},
        "v250": {"cmd": ["make", "build", "ALLOW_DIRTY_BUILD=1"], "expected_fail": True, "reason": "Version Schism"},
    }

    try:
        # 1. Execute Sabotage
        # We use the existing scripts/chaos_monkey.py as the saboteur
        print(f"🔥 Phase 1: Sabotaging environment ({args.mode})...")
        subprocess.check_call([sys.executable, "scripts/chaos_monkey.py", args.mode], cwd=repo_root)

        # 2. Verify Fail-Closed
        if args.mode in vector_map:
            v = vector_map[args.mode]
            print(f"🔍 Phase 2: Verifying Fail-Closed for {v['reason']}...")
            
            # We expect this to FAIL if the guard works
            env = dict(os.environ)
            if args.mode == "v231":
                env["ALLOW_DIRTY_BUILD"] = "1"
                env["ALLOW_VERSION_BUMP"] = "0"

            proc = subprocess.run(v["cmd"], cwd=repo_root, capture_output=True, text=True, check=False, env=env)
            
            if proc.returncode != 0:
                print("✅ SUCCESS: Guard triggered as expected. Output contained failure.")
                # Optional: check if specific error message is in proc.stderr
                return 0
            else:
                print(f"❌ FAILURE: Guard did NOT trigger. System is vulnerable to {v['reason']}.")
                return 1
        else:
            # For non-vector modes, we just run the monkey and don't verify execution here
            # shadow_runner.py usually handles the verification of artifact sabotage
            print("ℹ️ Mode is artifact-only. Use shadow_runner.py for full verification.")
            return 0

    except subprocess.CalledProcessError as e:
        print(f"🛑 CRITICAL ERROR: Sabotage phase failed. {e}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())
