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

def check_vaccine(error_message):
    """Check if a known vaccine exists for the given error message.
    
    Returns the resolution string if a matching vaccine is found, None otherwise.
    This enables autonomous self-healing: when a build fails, the system can
    suggest the exact fix before the operator even looks at the error.
    """
    init_ledger()
    with open(LEDGER_PATH, "r") as f:
        data = json.load(f)
    
    vaccines = data.get("vaccines", {})
    error_lower = error_message.lower()
    
    for code, info in vaccines.items():
        # Match if the vaccine code appears in the error message (case-insensitive)
        if code.lower() in error_lower or any(
            keyword in error_lower
            for keyword in code.lower().replace("_", " ").split()
        ):
            resolution = info.get("resolution", "No resolution documented.")
            print(f"💉 [ARCHIVIST] VACCINE FOUND for '{code}': {resolution}")
            return resolution
    
    return None

def show_ledger(last_n=20):
    """Pretty-print recent events from the Error Ledger in a human-friendly table."""
    init_ledger()
    with open(LEDGER_PATH, "r") as f:
        data = json.load(f)

    events = data.get("events", [])
    vaccines = data.get("vaccines", {})

    if not events:
        print("\n  🩺 ERROR LEDGER — No events recorded yet.")
        print("     System is clean. Nothing to report.\n")
        return

    # Show only last N
    display = events[-last_n:]

    # Colors for categories
    cat_colors = {
        "INFRA": "\033[96m",     # Cyan
        "METADATA": "\033[95m",  # Magenta
        "LOGIC": "\033[93m",     # Yellow
        "HYGIENE": "\033[92m",   # Green
        "IDENTITY": "\033[91m",  # Red
    }
    reset = "\033[0m"
    bold = "\033[1m"
    dim = "\033[2m"

    print(f"\n{bold}  🩺 ERROR LEDGER — Last {len(display)} of {len(events)} events{reset}")
    print(f"  {'─' * 88}")
    print(f"  {bold}{'TIMESTAMP':<22} {'CATEGORY':<12} {'GATE':<12} {'MESSAGE':<42}{reset}")
    print(f"  {'─' * 88}")

    for ev in display:
        ts = ev.get("timestamp_utc", "?")[:19].replace("T", " ")
        cat = ev.get("category", "?")
        gate = ev.get("gate", "?")
        msg = ev.get("message", "")
        res = ev.get("resolution")

        color = cat_colors.get(cat, "")
        # Truncate long messages for table display
        msg_display = (msg[:40] + "..") if len(msg) > 42 else msg

        print(f"  {dim}{ts}{reset} {color}{cat:<12}{reset} {gate:<12} {msg_display}")
        if res:
            print(f"  {' ' * 22} {dim}↳ Fix: {res}{reset}")

    print(f"  {'─' * 88}")

    # Vaccine summary
    if vaccines:
        print(f"\n{bold}  💉 VACCINES LEARNED: {len(vaccines)}{reset}")
        for code, info in vaccines.items():
            learned = info.get("learned_at", "?")[:10]
            sol = info.get("resolution", "?")
            print(f"     • {code}: {sol} {dim}({learned}){reset}")
        print()
    else:
        print(f"\n  {dim}No vaccines recorded yet.{reset}\n")


def main():
    parser = argparse.ArgumentParser(
        description="TRADER_OPS Error Archivist — Centralized Error Intelligence",
        epilog="Full guide: docs/COMMANDS.md"
    )
    parser.add_argument("--log", nargs=3, metavar=('CAT', 'MSG', 'GATE'), help="Log a new error")
    parser.add_argument("--learn", nargs=2, metavar=('CODE', 'SOL'), help="Learn a new resolution")
    parser.add_argument("--verify-ledger", action="store_true", help="Verify ledger integrity")
    parser.add_argument("--check-vaccine", metavar='MSG', help="Check if a vaccine exists for the given error")
    parser.add_argument("--show", action="store_true", help="Show recent errors (human-friendly table)")
    parser.add_argument("--last", type=int, default=20, help="Number of recent events to show (default: 20)")

    args = parser.parse_args()

    if args.show:
        show_ledger(args.last)
    elif args.log:
        log_event(args.log[0], args.log[1], args.log[2])
    elif args.learn:
        learn_from_failure(args.learn[0], args.learn[1])
    elif args.check_vaccine:
        result = check_vaccine(args.check_vaccine)
        if result:
            print(f"Resolution: {result}")
            sys.exit(0)
        else:
            print("[ARCHIVIST] No matching vaccine found.")
            sys.exit(1)
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
        print("[INFO] Error Archivist standby. Use --show to view errors, --help for all options.")

if __name__ == "__main__":
    main()
