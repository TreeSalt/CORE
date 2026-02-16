#!/usr/bin/env python3
"""
Sovereign Connector for TRADER_OPS Build System.
Delegates all logic to antigravity_harness.forge.
"""

import sys
from pathlib import Path

# Add repo root to path so we can import antigravity_harness
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from antigravity_harness.forge.build import build_drop_packet  # noqa: E402


def main():
    print("🔨 Sovereign Forge: Initializing...")
    dist_dir = REPO_ROOT / "dist"

    try:
        ledger = build_drop_packet(REPO_ROOT, dist_dir)
        print(f"✅ Build Complete. Version: {ledger['version']}")
        ledger_file = dist_dir / f"RUN_LEDGER_v{ledger['version']}.json"
        
        # Post-Build Verification: Fail-Closed Gate
        print("🛡️  Sovereign Gate: Executing Post-Build Verification...")
        import subprocess
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
        
        print("✅ POST-BUILD VERIFICATION PASSED.")
        print(f"📜 Ledger: {ledger_file}")
    except Exception as e:
        print(f"⛔ FATAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
