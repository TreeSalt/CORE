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
import re
import subprocess
import sys
from pathlib import Path

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

# ANTIGRAVITY HARNESS: Fortress Protocol
from antigravity_harness.forge.build import _sync_project_metadata, read_version  # noqa: E402
from antigravity_harness.paths import (  # noqa: E402
    CERT_DIR,
    DATA_DIR,
    INTEL_DIR,
    REPORT_DIR,
    SNAPSHOT_DIR,
    ensure_dirs,
)

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

    # Canonical manifests that we management
    manifests = [
        REPO_ROOT / "docs/ready_to_drop/COUNCIL_CANON.yaml",
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs/AGENT_ONBOARDING.md",
    ]

    if fix:
        for m in manifests:
            if m.exists():
                # Revert ANY local changes to manifests to ensure no sabotage (fingerprints, etc) persists.
                # We will re-sync the version immediately after.
                rel = m.relative_to(REPO_ROOT)
                print_status(f"Restoring {rel} to Golden State...", "WARN")
                subprocess.run(["git", "checkout", "HEAD", "--", str(rel)], cwd=REPO_ROOT, check=False)

    version_synced = True
    # Verify Canon
    canon_path = manifests[0]
    if canon_path.exists():
        content = canon_path.read_text()
        match = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', content)
        if not match or match.group(1) != current_version:
            print_status(f"Version mismatch: Code({current_version}) != Canon({match.group(1) if match else 'NONE'})", "WARN")
            version_synced = False

    # Verify README
    readme_path = manifests[1]
    if readme_path.exists():
        content = readme_path.read_text()
        if f"v{current_version}" not in content:
            print_status("README.md is out of date.", "WARN")
            version_synced = False

    if not version_synced:
        if fix:
            _sync_project_metadata(REPO_ROOT, current_version)
            print_status("Version synchronized across manifest chain.", "PASS")
            return True
        return False

    print_status("Version is synchronized.", "PASS")
    return True


def check_hygiene(fix=False):
    print_status("Checking Repository Hygiene...")
    if fix:
        print_status("Running automated deep-clean...")
        subprocess.run(
            [sys.executable, "-B", "scripts/clean_repo.py", "--clean", "--clean-generated"],
            cwd=REPO_ROOT,
            check=False,
        )
        if (REPO_ROOT / ".git").exists():
            print_status("Purging untracked and ignored artifacts (protecting identity)...")
            # Protect key and pub from clean sweep to maintain identity permanence
            subprocess.run(["git", "clean", "-fdx", "-e", "sovereign.key", "-e", "sovereign.pub"], cwd=REPO_ROOT, check=False)
        return True

    result = subprocess.run(
        [sys.executable, "-B", "scripts/clean_repo.py", "--verify-strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print_status("Hygiene violations detected.", "WARN")
        return False

    print_status("Hygiene is perfect.", "PASS")
    return True


def check_environment(fix=False):
    print_status("Checking Environment Anchors...")
    if fix:
        print_status("Repairing mandatory subdirectories...")
        ensure_dirs()
        # Restore missing tracked files (except __init__.py and identity)
        if (REPO_ROOT / ".git").exists():
            print_status("Restoring missing tracked files (git checkout)...")
            status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True)
            for line in status.splitlines():
                if line.startswith(" D "):
                    path = line[3:].strip().strip('"')
                    # Don't restore identity keys; we'll manage them surgically
                    if path not in ["antigravity_harness/__init__.py", "sovereign.pub", "sovereign.key"]:
                        subprocess.run(["git", "checkout", "HEAD", "--", path], cwd=REPO_ROOT, check=False)

        # Identity Restoration
        key_path = REPO_ROOT / "sovereign.key"
        pub_path = REPO_ROOT / "sovereign.pub"
        if key_path.exists():
            print_status("Synchronizing identity (sovereign.pub)...")
            subprocess.run(["openssl", "pkey", "-in", str(key_path), "-pubout", "-out", str(pub_path)], cwd=REPO_ROOT, check=False)
        else:
            # If we don't have a key but have a phantom pub key restored from Git, purge it
            # so a fresh pair can be generated during the build.
            if pub_path.exists():
                print_status("Purging orphaned public key to allow fresh identity generation...", "WARN")
                pub_path.unlink()
        return True

    # Verify-only
    for d in (DATA_DIR, SNAPSHOT_DIR, REPORT_DIR, CERT_DIR, INTEL_DIR):
        if not d.exists() or not d.is_dir():
            print_status(f"Missing anchor: {d.relative_to(REPO_ROOT)}", "WARN")
            return False

    print_status("Environment anchors present.", "PASS")
    return True


def git_surgeon(fix=False):
    """The 'Git Surgeon' auto-commits authorized mutations if the rest of the tree is clean."""
    if not fix:
        return True

    print_status("Initiating Git Surgery...")
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
    ).strip()
    if not status:
        print_status("Git tree is already clean.", "PASS")
        return True

    lines = status.split("\n")
    # Unified list from build.py + localized additions
    authorized = [
        "antigravity_harness/__init__.py",
        "README.md",
        "docs/ready_to_drop/COUNCIL_CANON.yaml",
        "docs/AGENT_ONBOARDING.md",
        "docs/ARCHITECTURE_MAP.md",
        "docs/DECISION_LOG.md",
        "skill.md",
        "sovereign.pub",  # Identity Binding
        "scripts/self_heal.py",  # Self-awareness
        "scripts/preflight.py",  # Infra
        "Makefile",  # Infra
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
        print_status(
            f"Git surgery aborted: Unexpected changes detected in {forbidden}", "FAIL"
        )
        return False

    if to_add:
        print_status(f"Auto-committing authorized mutations: {to_add}...")
        subprocess.run(["git", "add"] + to_add, cwd=REPO_ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: self-healing synchronization of project state"],
            cwd=REPO_ROOT,
            check=True,
        )
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
