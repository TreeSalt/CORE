#!/usr/bin/env python3
"""
scripts/autopilot_supervisor.py
===============================
v4.5.82 - Autopilot Safety Supervisor (Build/Verify/Run Guardrails)
Unified entrypoint for build auditing and paper execution safety.
"""

import argparse
import os
import subprocess
import sys
import json
import yaml
from pathlib import Path
from typing import List, Optional

from antigravity_harness.strategies.registry import STRATEGY_REGISTRY

# ANSI Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Paths
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

def log_info(msg: str):
    print(f"[{BOLD}INFO{RESET}] {msg}")

def log_success(msg: str):
    print(f"[{GREEN}PASS{RESET}] {msg}")

def log_error(msg: str):
    print(f"[{RED}FAIL{RESET}] {msg}", file=sys.stderr)

def log_warn(msg: str):
    print(f"[{YELLOW}WARN{RESET}] {msg}")

def run_cmd(args: List[str], cwd: Path = REPO_ROOT) -> int:
    """Run a command and return exit code."""
    try:
        res = subprocess.run(args, cwd=cwd, check=False)
        return res.returncode
    except Exception as e:
        log_error(f"Execution Error: {e}")
        return 1

def find_latest_drop(dist_dir: Path) -> Optional[Path]:
    """Find the latest READY_TO_DROP zip in dist/."""
    zips = list(dist_dir.glob("TRADER_OPS_READY_TO_DROP_*.zip"))
    if not zips:
        return None
    # Sort by name (which includes version)
    zips.sort()
    return zips[-1]

def cmd_verify(dist_dir: Path) -> bool:
    """Implement the 'verify' logic."""
    log_info(f"Auditing artifacts in {dist_dir}...")
    
    drop_zip = find_latest_drop(dist_dir)
    if not drop_zip:
        log_error(f"No READY_TO_DROP zip found in {dist_dir}")
        return False
    
    version_match = drop_zip.name.split("_v")[-1].replace(".zip", "")
    ledger_path = dist_dir / f"RUN_LEDGER_v{version_match}.json"
    
    log_info(f"Targeting version: {version_match}")
    log_info(f"Drop Zip: {drop_zip}")
    
    # 1. Run Drop Auditor (Institutional Scan)
    log_info("Running Drop Auditor...")
    pub_key = REPO_ROOT / "sovereign.pub"
    if run_cmd(["python3", "scripts/drop_auditor.py", "--drop", str(drop_zip), "--pub", str(pub_key)]) != 0:
        log_error("Drop Auditor failed.")
        return False
    
    # 2. Run Verify Drop Packet (Fiduciary Gate)
    log_info("Running Verify Drop Packet...")
    if run_cmd(["python3", "scripts/verify_drop_packet.py", "--strict", "--drop", str(drop_zip), "--run-ledger", str(ledger_path)]) != 0:
        log_error("Fiduciary Gate failed.")
        return False
    
    log_success("Artifact Integrity & Fiduciary Chain Verified.")
    return True

def cmd_run_paper(strategy: str, profile_path: Path, dist_dir: Path) -> None:
    """Implement the 'run-paper' logic."""
    # 1. Mandatory Verify
    if not cmd_verify(dist_dir):
        log_error("VERIFICATION FAILED. Refusing to start paper run.")
        sys.exit(1)
        
    log_info(f"Initiating Safety Supervisor for Paper Run: {strategy}")
    
    # 2. Strategy Governance Checks
    try:
        # Check registration
        STRATEGY_REGISTRY.verify_strategy_allowed(strategy, mode="paper")
    except Exception as e:
        log_error(f"GOVERNANCE VIOLATION: {e}")
        sys.exit(1)
        
    log_success(f"Governance Check Passed: {strategy} is authorized for Paper.")
    
    # 3. Safety Profile Enforcement
    if not profile_path.exists():
        log_error(f"Profile not found: {profile_path}")
        sys.exit(1)
        
    try:
        with open(profile_path, "r") as f:
            profile = yaml.safe_load(f)
    except Exception as e:
        log_error(f"Failed to parse profile {profile_path}: {e}")
        sys.exit(1)
        
    # Required Fields Check
    required_risk = ["daily_loss_cap_usd", "max_position_size_contracts"]
    for field in required_risk:
        if field not in profile.get("risk", {}):
            log_error(f"SAFETY VIOLATION: Missing required risk field '{field}' in profile.")
            sys.exit(1)
            
    # Permissions
    if profile.get("permissions", {}).get("live_trading_enabled", True):
        log_error("SAFETY VIOLATION: 'live_trading_enabled' must be false for paper mode.")
        sys.exit(1)
        
    # News Blackout
    if not profile.get("news_blackout", {}).get("enabled", False):
        log_warn("Safety Advisory: News blackout is disabled in profile.")
    
    log_success("Safety Profile Constraints Verified.")
    
    # 4. Ready to Run
    print(f"\n{BOLD}{GREEN}>>> AUTOPILOT SAFETY SUPERVISOR: SYSTEM READY <<<{RESET}")
    print(f"Strategy: {strategy}")
    print(f"Profile:  {profile['profile_id']}")
    print(f"Mode:     PAPER")
    print(f"Status:   AUTHORIZED")

def main():
    parser = argparse.ArgumentParser(description="Autopilot Safety Supervisor")
    subparsers = parser.add_subparsers(dest="command")
    
    # Verify command
    verify_p = subparsers.add_parser("verify", help="Audit latest build artifacts")
    verify_p.add_argument("--dist", default="dist", help="Path to dist directory")
    
    # Run Paper command
    run_p = subparsers.add_parser("run-paper", help="Run strategy in paper mode with safety checks")
    run_p.add_argument("--strategy", required=True, help="Strategy ID")
    run_p.add_argument("--profile", default="profiles/seed_profile.yaml", help="Safety profile PATH")
    run_p.add_argument("--dist", default="dist", help="Path to dist directory for verification")
    
    args = parser.parse_args()
    
    if args.command == "verify":
        if not cmd_verify(Path(args.dist)):
            sys.exit(1)
    elif args.command == "run-paper":
        cmd_run_paper(args.strategy, Path(args.profile), Path(args.dist))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
