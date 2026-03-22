#!/usr/bin/env python3
"""
Negative Test Suite for Strategy Governance.
Verifies that the system correctly blocks:
1. Unregistered strategies.
2. Tampered strategies (hash mismatch).
3. Incorrect tier usage (e.g. Lab in Live mode).
"""

import os
import subprocess
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
STRATEGY_REGISTRY_JSON = REPO_ROOT / "mantis_core" / "strategies" / "STRATEGY_REGISTRY.json"

def run_cmd(args):
    """Run a CLI command and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    res = subprocess.run(args, capture_output=True, text=True, env=env, check=False)
    return res.returncode, res.stdout, res.stderr

def test_unregistered():
    print("Test 1: Unregistered Strategy")
    # v999_fake is not in the registry
    code, out, err = run_cmd(["python3", "-m", "mantis_core.cli", "validate", "--strategy", "v999_fake", "--symbol", "BTC"])
    if code != 0 and "GOV-001 UNREGISTERED" in err:
        print("  ✅ PASS: Correctly blocked unregistered strategy.")
    else:
        print(f"  ❌ FAIL: Expected GOV-001, got code {code}. Stderr: {err}")

def test_tampered():
    print("Test 2: Tampered Strategy (Hash Mismatch)")
    # Tamper with v032_simple by adding a comment
    strat_file = REPO_ROOT / "mantis_core" / "strategies" / "quarantine" / "v032_simple" / "v032_simple.py"
    original_content = strat_file.read_text()
    
    try:
        strat_file.write_text(original_content + "\n# TAMPERED\n")
        code, out, err = run_cmd(["python3", "-m", "mantis_core.cli", "validate", "--strategy", "v032_simple", "--symbol", "BTC"])
        if code != 0 and "GOV-002 HASH_MISMATCH" in err:
            print("  ✅ PASS: Correctly detected tampered file.")
        else:
            print(f"  ❌ FAIL: Expected GOV-002, got code {code}. Stderr: {err}")
    finally:
        # Restore
        strat_file.write_text(original_content)

def test_tier_violation():
    print("Test 3: Tier Violation (Lab in Live mode)")
    # v032_simple is 'quarantine'. Live mode only allows 'certified'.
    # Note: we need to trigger a command that uses 'live' mode.
    # In cli.py, 'emit-signals' enforces 'live' mode.
    code, out, err = run_cmd(["python3", "-m", "mantis_core.cli", "emit-signals", "--strategy", "v032_simple", "--symbol", "BTC"])
    if code != 0 and "GOV-003 TIER_BLOCKED" in err:
        print("  ✅ PASS: Correctly blocked low-tier strategy in live mode.")
    else:
        print(f"  ❌ FAIL: Expected GOV-003, got code {code}. Stderr: {err}")

def test_valid_certified():
    print("Test 4: Certified Strategy in Research Mode")
    # v080_volatility_guard_trend is certified. Should pass research mode.
    code, out, err = run_cmd(["python3", "-m", "mantis_core.cli", "validate", "--strategy", "v080_volatility_guard_trend", "--symbol", "BTC", "--start", "2024-01-01", "--end", "2024-01-02", "--interval", "1d"])
    if code == 0:
        print("  ✅ PASS: Certified strategy allowed in research mode.")
    else:
        print(f"  ❌ FAIL: Expected success, got code {code}. Stderr: {err}")

if __name__ == "__main__":
    print("--- GOVERNANCE GATE NEGATIVE TESTS ---")
    test_unregistered()
    test_tampered()
    test_tier_violation()
    test_valid_certified()
    print("---------------------------------------")
