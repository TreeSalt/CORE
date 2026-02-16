#!/usr/bin/env python3
"""
chaos_sweep.py — The Ultimate Stress Tester.
Iteratively executes every known Hydra vector and verifies the Fail-Closed state.
"""

import subprocess
import sys
from pathlib import Path

# Mocked vector map from chaos_hydra_monkey.py
VECTORS = [
    "v227", "v228", "v240", "v231", "v241", "v242", "v243", "v244", "v245", 
    "v246", "v247", "v248", "v249", "v250", "v251", "v252", "v253", "v254", 
    "v255", "v256", "v257", "v258", "v259", "v260", "v261", "v262"
]

def main():
    root = Path(__file__).parent.parent.resolve()
    print("🐉 UNLEASHING CHAOS SWEEP (Recursive Verification)")
    print("---------------------------------------------")

    results = []

    for v in VECTORS:
        print(f"\n🚀 VECTOR: {v}")
        
        # 1. Clean Baseline
        print("  🧹 Resetting environment...")
        subprocess.run(["git", "restore", "."], cwd=root, check=True)
        # Ensure a fresh build is present for artifact sabotages
        if v in ["v251", "v252", "v253", "v254", "v259", "v260", "v261", "v262"]:
            print("  🔨 Building fresh drop packet for artifact sabotage...")
            subprocess.run(["python3", "-B", "scripts/make_drop_packet.py"], cwd=root, capture_output=True)

        # 2. Execute Stress Test
        print(f"  🔥 Unleashing Chaos Hydra Monkey: {v}")
        proc = subprocess.run([sys.executable, "scripts/chaos_hydra_monkey.py", "--mode", v], 
                              cwd=root, capture_output=True, text=True)
        
        if proc.returncode == 0:
            print(f"  ✅ PASS: {v} fail-closed verified.")
            results.append((v, "PASS"))
        else:
            print(f"  ❌ FAIL: {v} security guard bypassed!")
            print(proc.stdout)
            print(proc.stderr)
            results.append((v, "FAIL"))

    print("\n---------------------------------------------")
    print("🏁 CHAOS SWEEP COMPLETE")
    failed = [v for v, r in results if r == "FAIL"]
    if failed:
        print(f"🛑 VULNERABILITIES DETECTED: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("✅ ALL GATES SECURED. SYSTEM IS DRAGONPROOF.")
        sys.exit(0)

if __name__ == "__main__":
    main()
