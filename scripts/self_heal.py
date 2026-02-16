#!/usr/bin/env python3
"""
REPO DOCTOR — TRADER_OPS Self-Healing Protocol
==============================================
Automatically repairs common repository blockers:
1. Version Synchronization (Code -> Canon, README, Docs)
2. Hygiene Restoration (Cleaning forbidden artifacts)
3. Environment Anchoring (Ensuring required directories exist)
4. Git Sovereignty (Auto-committing authorized mutations)

Usage:
    python3 scripts/self_heal.py --fix
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

from antigravity_harness.forge.build import read_version, _sync_project_metadata

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_status(msg, status="INFO"):
    color = {"INFO": BOLD, "PASS": GREEN, "FAIL": RED, "WARN": YELLOW}.get(status, BOLD)
    print(f"{color}[{status}]{RESET} {msg}")


def check_version_sync(fix=False):
    print_status("Checking Version Synchronization...")
    init_path = REPO_ROOT / "antigravity_harness/__init__.py"
    current_version = read_version(init_path)
    
    # Check Canon
    canon_path = REPO_ROOT / "docs/ready_to_drop/COUNCIL_CANON.yaml"
    if canon_path.exists():
        content = canon_path.read_text()
        match = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', content)
        if not match or match.group(1) != current_version:
            print_status(f"Version mismatch: Code({current_version}) != Canon({match.group(1) if match else 'NONE'})", "WARN")
            if fix:
                _sync_project_metadata(REPO_ROOT, current_version)
                print_status("Version synchronized across Canon and Docs.", "PASS")
                return True
            return False
    
    # Check README
    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        if f"v{current_version}" not in content:
            print_status("README.md is out of date.", "WARN")
            if fix:
                _sync_project_metadata(REPO_ROOT, current_version)
                print_status("README.md updated.", "PASS")
                return True
    
    print_status("Version is synchronized.", "PASS")
    return True


def check_hygiene(fix=False):
    print_status("Checking Repository Hygiene...")
    if fix:
        print_status("Running automated deep-clean...")
        subprocess.run([sys.executable, "-B", "scripts/clean_repo.py", "--clean"], cwd=REPO_ROOT)
        return True
    
    result = subprocess.run([sys.executable, "-B", "scripts/clean_repo.py", "--verify-strict"], cwd=REPO_ROOT, capture_output=True)
    if result.returncode != 0:
        print_status("Hygiene violations detected.", "WARN")
        return False
    
    print_status("Hygiene is perfect.", "PASS")
    return True


def check_environment(fix=False):
    print_status("Checking Environment Anchors...")
    required_dirs = ["reports", "dist", "logs", "data"]
    missing = []
    for d in required_dirs:
        path = REPO_ROOT / d
        if not path.exists():
            missing.append(d)
    
    if missing:
        print_status(f"Missing directories: {missing}", "WARN")
        if fix:
            for d in missing:
                (REPO_ROOT / d).mkdir(parents=True, exist_ok=True)
                print_status(f"Created directory: {d}", "PASS")
            return True
        return False
    
    print_status("Environment anchors present.", "PASS")
    return True


def git_surgeon(fix=False):
    """The 'Git Surgeon' auto-commits authorized mutations if the rest of the tree is clean."""
    if not fix:
        return True
        
    print_status("Initiating Git Surgery...")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip()
    if not status:
        print_status("Git tree is already clean.", "PASS")
        return True
    
    lines = status.split("\n")
    authorized = [
        "antigravity_harness/__init__.py",
        "README.md",
        "docs/ready_to_drop/COUNCIL_CANON.yaml",
        "docs/AGENT_ONBOARDING.md",
        "docs/ARCHITECTURE_MAP.md",
        "docs/DECISION_LOG.md",
        "skill.md"
    ]
    
    to_add = []
    forbidden = []
    for line in lines:
        path = line[2:].strip().strip('"')
        if any(path.endswith(a) for a in authorized):
            to_add.append(path)
        else:
            forbidden.append(path)
            
    if forbidden:
        print_status(f"Git surgery aborted: Unexpected changes detected in {forbidden}", "FAIL")
        return False
    
    if to_add:
        print_status(f"Auto-committing authorized mutations: {to_add}...")
        subprocess.run(["git", "add"] + to_add, cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "chore: self-healing synchronization of project state"], cwd=REPO_ROOT, check=True)
        print_status("Surgery successful: Mutations persisted.", "PASS")
        return True
        
    return True


def main():
    parser = argparse.ArgumentParser(description="TRADER_OPS Repo Doctor")
    parser.add_argument("--fix", action="store_true", help="Apply repairs automatically")
    args = parser.parse_args()

    print(f"\n{BOLD}🛡️  REPO DOCTOR: TRADER_OPS Self-Healing Protocol{RESET}")
    print("=" * 60)

    success = True
    
    # 1. Environment
    if not check_environment(args.fix):
        success = False
        
    # 2. Versioning
    if not check_version_sync(args.fix):
        success = False
        
    # 3. Hygiene
    if not check_hygiene(args.fix):
        success = False
        
    # 4. Git (The Final Seal)
    if not git_surgeon(args.fix):
        success = False

    print("=" * 60)
    if success:
        print(f"{BOLD}{GREEN}✅ SYSTEM HEALED / VERIFIED{RESET}")
        sys.exit(0)
    else:
        print(f"{BOLD}{RED}❌ HEALING INCOMPLETE - Manual intervention required.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
