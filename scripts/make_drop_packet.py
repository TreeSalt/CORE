#!/usr/bin/env python3
"""
Sovereign Connector for TRADER_OPS Build System.
Delegates all logic to mantis_core.forge.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add repo root to path so we can import mantis_core
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mantis_core.forge.build import build_drop_packet  # noqa: E402

# ANTIGRAVITY HARNESS: Autonomous Error Intelligence
try:
    from scripts.archivist import log_event, check_vaccine  # noqa: E402
except ImportError:
    def log_event(*args, **kwargs): pass  # noqa: E302
    def check_vaccine(*args, **kwargs): return None  # noqa: E302


def main():
    parser = argparse.ArgumentParser(description="Sovereign Connector for TRADER_OPS Build System.")
    parser.add_argument("--out-dir", type=str, default="dist", help="Output directory for drop packet.")
    parser.add_argument("--no-bump", action="store_true", help="Skip automatic version bumping.")
    args = parser.parse_args()

    if args.no_bump:
        os.environ["SKIP_VERSION_BUMP"] = "1"

    print("🔨 Sovereign Forge: Initializing...")
    dist_dir = Path(args.out_dir)
    if not dist_dir.is_absolute():
        dist_dir = REPO_ROOT / dist_dir

    try:
        ledger = build_drop_packet(REPO_ROOT, dist_dir)
        print(f"✅ Build Complete. Version: {ledger['version']}")
        ledger_file = dist_dir / f"RUN_LEDGER_v{ledger['version']}.json"
        
        # Post-Build Verification: Fail-Closed Gate
        print("🛡️  Sovereign Gate: Executing Post-Build Verification...")
        drop_zip = dist_dir / f"TRADER_OPS_READY_TO_DROP_v{ledger['version']}.zip"
        
        # Run verify_drop_packet.py
        subprocess.check_call([
            sys.executable, str(REPO_ROOT / "scripts/verify_drop_packet.py"),
            "--drop", str(drop_zip),
            "--run-ledger", str(ledger_file)
        ])
        
        # Run verify_certificate.py
        # Note: We need to point it to the evidence zip which is inside dist now
        evidence_zip = dist_dir / f"TRADER_OPS_EVIDENCE_v{ledger['version']}.zip"
        subprocess.check_call([
            sys.executable, str(REPO_ROOT / "scripts/verify_certificate.py"),
            "--evidence", str(evidence_zip)
        ])

        # Run verify_run_ledger_signature.py
        # We just signed it, so we verify it immediately to close the loop
        ledger_sig = dist_dir / f"RUN_LEDGER_v{ledger['version']}.json.sig"
        subprocess.check_call([
            sys.executable, str(REPO_ROOT / "scripts/verify_run_ledger_signature.py"),
            "--run-ledger", str(ledger_file),
            "--sig", str(ledger_sig)
        ])
        
        # Generate Gate Report (Fail-Closed Artifact)
        
        # Enforce target version binding for trust parity
        target_version = os.environ.get("TARGET_VERSION")
        if target_version and target_version.lstrip("v") != ledger['version']:
            raise ValueError(f"Version Mismatch: Built v{ledger['version']} but TARGET_VERSION={target_version}")
            
        gate_report = {
            "version": ledger['version'],
            "timestamp_utc": ledger['timestamp_utc'],
            "gates": {
                "pubkey_pin_verification": "PASS",
                "certificate_signature": "PASS",
                "run_ledger_signature": "PASS",
                "manifest_integrity": "PASS",
                "timeline_sovereignty": "PASS"
            }
        }
        gate_report_path = dist_dir / "gate_report.json"
        with open(gate_report_path, "w") as f:
            json.dump(gate_report, f, indent=2)
        print(f"✅ Gate Report Generated: {gate_report_path}")
        
        print("✅ POST-BUILD VERIFICATION PASSED.")
        print(f"📜 Ledger: {ledger_file}")
    except Exception as e:
        error_msg = str(e)
        print(f"⛔ FATAL: {error_msg}")

        # Autonomous Error Intelligence: Log to ERROR_LEDGER.json
        category = "LOGIC"
        if "SECURITY" in error_msg.upper() or "SABOTAGE" in error_msg.upper():
            category = "IDENTITY"
        elif "PURITY" in error_msg.upper() or "HYGIENE" in error_msg.upper():
            category = "HYGIENE"
        elif "STRICT" in error_msg.upper() or "ANCHOR" in error_msg.upper():
            category = "METADATA"
        log_event(category, error_msg, "RUNTIME")

        # Autonomous Self-Healing Hint: Check for known vaccines
        vaccine = check_vaccine(error_msg)
        if vaccine:
            print(f"💡 SUGGESTED FIX: {vaccine}")

        sys.exit(1)


if __name__ == "__main__":
    main()
