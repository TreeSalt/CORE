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
import hashlib
import re
import subprocess
import sys
from pathlib import Path

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

# ANTIGRAVITY HARNESS: Fortress Protocol
from antigravity_harness.forge.build import _sync_project_metadata, bump_version, read_version  # noqa: E402
from antigravity_harness.paths import (  # noqa: E402
    CERT_DIR,
    DATA_DIR,
    INTEL_DIR,
    REPORT_DIR,
    SNAPSHOT_DIR,
    ensure_dirs,
)
from scripts.archivist import log_event  # noqa: E402

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
        REPO_ROOT / "setup.py",
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
            
    # Verify setup.py
    setup_path = manifests[3]
    if setup_path.exists():
        content = setup_path.read_text()
        if f'version="{current_version}"' not in content:
            print_status("setup.py is out of date.", "WARN")
            version_synced = False

    if not version_synced:
        if fix:
            _sync_project_metadata(REPO_ROOT, current_version)
            log_event("METADATA", f"Synchronized project version to {current_version}", "RECOVERY", "Auto-Sync")
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
            print_status("Purging untracked and ignored artifacts (protecting identity and ledger)...")
            # Protect key, pub, and ledger from clean sweep to maintain institutional memory
            subprocess.run(
                ["git", "clean", "-fdx", "-e", "sovereign.key", "-e", "sovereign.pub", "-e", "05_DATA_CACHE/ERROR_LEDGER.json"],
                cwd=REPO_ROOT,
                check=False,
            )
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
                        log_event("INFRA", f"Restoring missing tracked file: {path}", "RECOVERY", "Git Checkout")
                        subprocess.run(["git", "checkout", "HEAD", "--", path], cwd=REPO_ROOT, check=False)

        # Identity Restoration
        key_path = REPO_ROOT / "sovereign.key"
        pub_path = REPO_ROOT / "sovereign.pub"
        if key_path.exists():
            print_status("Synchronizing identity (sovereign.pub)...")
            subprocess.run(["openssl", "pkey", "-in", str(key_path), "-pubout", "-out", str(pub_path)], cwd=REPO_ROOT, check=False)
        elif pub_path.exists():
            # If we don't have a key but have a phantom pub key restored from Git, purge it
            # so a fresh pair can be generated during the build.
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


def verify_authorized_list_integrity(authorized: list) -> bool:
    """Verifies that the authorized mutation list has not been tampered with."""
    EXPECTED_HASH = "1005210f1a1fa4ab9695a39da52989fd43268aea7c33d397ee4f8f7e979b6d01"
    actual_hash = hashlib.sha256("".join(authorized).encode()).hexdigest()
    if actual_hash != EXPECTED_HASH:
        print_status(f"INTEGRITY BREACH: Authorized list tampered! (Hash: {actual_hash[:8]}...)", "FAIL")
        return False
    return True


def check_untracked_sh_py() -> bool:
    """Detects untracked .py or .sh files in the source tree (Persistence Guard)."""
    # Scan antigravity_harness/ for untracked executables
    try:
        status = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "antigravity_harness/"],
            cwd=REPO_ROOT, text=True
        ).strip()
        if status:
            untracked_executables = []
            for line in status.splitlines():
                if line.endswith((".py", ".sh")):
                    untracked_executables.append(line)
            
            if untracked_executables:
                print_status(f"SECURITY VIOLATION: Untracked executables in source tree: {untracked_executables}", "FAIL")
                return False
    except subprocess.CalledProcessError:
        pass # Not a git repo or other issue
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
        "scripts/archivist.py",  # Memory
        "05_DATA_CACHE/ERROR_LEDGER.json", # Memory
        "Makefile",  # Infra
        "setup.py",  # Packaging
        "antigravity_harness/forge/build.py", # Forge logic
        "scripts/ibkr_ingest_mes_5m.py", # IBKR
        "scripts/verify_drop_packet.py", # Verification
        "docs/COMMANDS.md", # Documentation
        "requirements-ibkr.txt", # Dependencies
        "prompts/missions/", # Mission Records
        "scripts/strategy_governance.py", # Governance Tool
        "scripts/verify_governance_gates.py", # Governance Verification
        "antigravity_harness/strategies/STRATEGY_REGISTRY.json", # Registry
        "antigravity_harness/strategies/registry.py", # Registry Logic
        "antigravity_harness/strategies/__init__.py", # Strategy Exports
        "antigravity_harness/strategies/", # Strategy Folders (Recursive matching via startswith)
        # Deep recursion for moved strategies
        "antigravity_harness/strategies/quarantine/", 
        "antigravity_harness/strategies/lab/",
        "antigravity_harness/strategies/certified/",
        "antigravity_harness/cli.py", # CLI Governance Hooks
        "antigravity_harness/tests/test_v31.py", # Test Updates for Governance
        "antigravity_harness/tests/test_golden_cert.py", # Test Updates for Governance
        "antigravity_harness/tests/test_distributed.py", # Test Updates for Governance
        "antigravity_harness/tests/test_v080_dynamic.py", # Test Updates for Governance
        "antigravity_harness/tests/test_suite.py", # Test Updates for Governance
        "antigravity_harness/tests/test_portfolio_engine.py", # Test Updates for Governance
        "antigravity_harness/tests/test_cli_alias.py", # Test Updates for Governance
        "tests/test_portfolio_router.py", # Test Updates for Governance
        "tests/test_portfolio_safety.py", # Test Updates for Governance
        "scripts/autopilot_supervisor.py", # Autopilot Supervisor (v4.5.82)
        "scripts/council_packet.py",       # Council Packet Generator (v4.5.82)
        "antigravity_harness/trust_root.py", # Trust Root (v4.5.109)
        "scripts/verify_run_ledger_signature.py", # Ledger Verify (v4.5.109)
        "keys/", # Sovereign Pubkey Dir (v4.5.109)
        "scripts/drop_auditor.py", # Fiduciary Update (v4.5.109)
        "scripts/one_true_command.sh", # Fiduciary Update (v4.5.109)
        "scripts/verify_certificate.py", # Fiduciary Update (v4.5.109)
        "docs/ready_to_drop/PAYLOAD_MANIFEST.json", # Fiduciary Manifest (v4.5.115)
        "antigravity_harness/execution/fill_tape.py", # Hardening Dir Persistence (v4.5.123)
        "Makefile", # Dataset & Hardening (v4.5.123)
        "antigravity_harness/portfolio_engine.py", # Performance Opt (v4.5.123)
        "antigravity_harness/portfolio_router.py", # Performance Opt (v4.5.123)
        "antigravity_harness/regimes.py", # Performance Opt (v4.5.123)
        "tests/test_safety_integration.py", # Performance Opt (v4.5.123)
        "antigravity_harness/execution/ibkr_adapter.py", # Fiduciary Bridge (v4.5.148)
        "scripts/ibkr_paper_execute.py", # Fiduciary Bridge (v4.5.148)
        "antigravity_harness/accelerators/", # Item 2 Vectorized Scaling
        "antigravity_harness/context.py", # Item 2 Vectorized Scaling
        "antigravity_harness/models.py", # Item 2 Vectorized Scaling
        "antigravity_harness/calibration.py", # Item 2 Vectorized Scaling
        "antigravity_harness/gates.py", # Item 2 Vectorized Scaling
        "scripts/verify_signatures.py", # Item 3 Sovereign Auditor V2
        "antigravity_harness/portfolio_regime_report.py", # Item 4 Multi-Asset Regime Alpha
        "scripts/vuln_scanner.py", # Item 5 Zero-Day Vulnerability Scrub
        "scripts/clean_repo.py", # Item 5 Zero-Day Vulnerability Scrub
        "antigravity_harness/tests/test_v5_security.py", # Item 5 Zero-Day Vulnerability Scrub
        "antigravity_harness/config.py", # Item 6 Autonomous Plateau Sizing
        "antigravity_harness/engine.py", # Item 6 Autonomous Plateau Sizing
        "antigravity_harness/tests/test_sizing.py", # Item 6 Autonomous Plateau Sizing
        "antigravity_harness/metrics.py", # Item 7 Kelly Criterion Sizing
        "antigravity_harness/tests/test_kelly_sizing.py", # Item 7 Kelly Criterion Sizing
    ]

    # V4 Integrity Seal
    if not verify_authorized_list_integrity(authorized):
        return False

    to_add = []
    forbidden = []
    for line in lines:
        path = line[2:].strip().strip('"')
        if any(path.endswith(a) for a in authorized) or any(path.startswith(a) for a in authorized):
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
    parser.add_argument("--bump", action="store_true", help="Increment version number (Patch bump)")
    args = parser.parse_args()

    print(f"\n{BOLD}🛡️  REPO DOCTOR: TRADER_OPS Self-Healing Protocol{RESET}")
    print("=" * 60)

    success = True

    # 0. Version Bump (Optional, controlled by preflight)
    if args.bump and args.fix:
        print_status("Initiating Institutional Version Bump...")
        bump_version(REPO_ROOT / "antigravity_harness/__init__.py")

    # 1. Environment
    if not check_environment(args.fix):
        success = False

    # 2. Security (Persistence Guard)
    print_status("Checking Security (Persistence Guard)...")
    if not check_untracked_sh_py():
        success = False
        print_status("Security violation detected!", "FAIL")

    # 3. Versioning
    if not check_version_sync(args.fix):
        success = False

    # 4. Hygiene
    if not check_hygiene(args.fix):
        success = False

    # 5. Git (The Final Seal)
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
