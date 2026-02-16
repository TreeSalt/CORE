#!/usr/bin/env python3
"""
THE ARCHIVIST — Error Classification & Learning Protocol
=========================================================
Centralized intelligence for TRADER_OPS error lifecycle:
1. Classification (Categorizing failures into INFRA|METADATA|LOGIC|HYGIENE)
2. Categorization (Startup|Runtime|Shutdown)
3. Learning (Documenting vaccinations/resolutions)

Managed Artifact: 05_DATA_CACHE/ERROR_LEDGER.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
LEDGER_PATH = REPO_ROOT / "05_DATA_CACHE/ERROR_LEDGER.json"

# Taxonomy
CATEGORIES = ["INFRA", "METADATA", "LOGIC", "HYGIENE", "IDENTITY"]
GATES = ["STARTUP", "RUNTIME", "SHUTDOWN", "RECOVERY"]

def init_ledger():
    """Ensure the ledger exists with a clean structure."""
    if not LEDGER_PATH.parent.exists():
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not LEDGER_PATH.exists():
        data = {
            "system_start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "events": [],
            "vaccines": {}
        }
        with open(LEDGER_PATH, "w") as f:
            json.dump(data, f, indent=4)

def log_event(category, message, gate, resolution=None):
    """Logs a system event or failure with classification."""
    init_ledger()
    
    if category not in CATEGORIES:
        category = "LOGIC" # Default
    if gate not in GATES:
        gate = "RUNTIME"
        
    event = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "category": category,
        "gate": gate,
        "message": message,
        "resolution": resolution
    }
    
    with open(LEDGER_PATH, "r") as f:
        data = json.load(f)
    
    data["events"].append(event)
    
    # Prune events to last 100 to prevent bloat
    if len(data["events"]) > 100:
        data["events"] = data["events"][-100:]
        
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"[ARCHIVIST] Logged {category} failure at {gate} gate.")

def learn_from_failure(error_code, solution):
    """Documents a 'vaccine' for a specific error pattern."""
    init_ledger()
    with open(LEDGER_PATH, "r") as f:
        data = json.load(f)
        
    data["vaccines"][error_code] = {
        "learned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resolution": solution
    }
    
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[ARCHIVIST] Learned new vaccine for: {error_code}")

def main():
    parser = argparse.ArgumentParser(description="TRADER_OPS Error Archivist")
    parser.add_argument("--log", nargs=3, metavar=('CAT', 'MSG', 'GATE'), help="Log a new error")
    parser.add_argument("--learn", nargs=2, metavar=('CODE', 'SOL'), help="Learn a new resolution")
    parser.add_argument("--verify-ledger", action="store_true", help="Verify ledger integrity")
    
    args = parser.parse_args()
    
    if args.log:
        log_event(args.log[0], args.log[1], args.log[2])
    elif args.learn:
        learn_from_failure(args.learn[0], args.learn[1])
    elif args.verify_ledger:
        if LEDGER_PATH.exists():
            print(f"[PASS] Error Ledger present: {LEDGER_PATH}")
            # Quick syntax check
            with open(LEDGER_PATH, "r") as f:
                json.load(f)
            sys.exit(0)
        else:
            print("[FAIL] Ledger missing.")
            sys.exit(1)
    else:
        init_ledger()
        print("[INFO] Error Archivist standby.")

if __name__ == "__main__":
    main()
