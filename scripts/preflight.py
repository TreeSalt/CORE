#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

# ANTIGRAVITY HARNESS: Error Classification
try:
    from scripts.archivist import log_event  # noqa: E402, I001
except ImportError:
    # Failsafe if run in isolation/bootstrapping
    def log_event(*args, **kwargs): pass

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Task 1: Institutional Cleanliness (Bytecode Prevention)
sys.dont_write_bytecode = True


def run_cmd(cmd: list, cwd: Path, env: Optional[dict] = None) -> bool:
    print(f"🚀 RUN: {' '.join(cmd)}")
    try:
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        # Task 5: Eliminate shell=True for institutional security
        result = subprocess.run(cmd, shell=False, check=False, cwd=cwd, env=current_env)
        if result.returncode == 0:
            print("   ✅ PASS")
            return True
        else:
            print(f"   ❌ FAIL (Exit Code: {result.returncode})")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def main() -> None:  # noqa: PLR0912, PLR0915
    """Antigravity Preflight main logic."""
    parser = argparse.ArgumentParser(description="Antigravity Preflight")
    parser.add_argument("--auto-clean", action="store_true", help="Clean repo before verification")
    parser.add_argument("--heal", action="store_true", help="Automatically repair versioning and hygiene blockers")
    parser.add_argument("--qa", action="store_true", help="Run static quality gates (ruff + mypy)")
    args = parser.parse_args()

    # Task 3: Global bytecode suppression
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    print("🛫 ANTIGRAVITY PREFLIGHT CHECK (Institutional Mode)")
    print("--------------------------------")

    root = Path(__file__).parent.parent.resolve()
    success = True

    # 0. Security Audit (Zero-Day Guard)
    print(f"{BOLD}🛡️  INITIATING VULNERABILITY SCAN...{RESET}")
    if not run_cmd([sys.executable, "-B", "scripts/vuln_scanner.py"], root):
        print("   ❌ FAIL: Security audit detected vulnerabilities. Build aborted.")
        sys.exit(1)

    # 0.1 Self-Healing (Proactive Restoration)
    if args.heal:
        print(f"{BOLD}🩹 INITIATING SELF-HEALING...{RESET}")
        cmd = [sys.executable, "-B", "scripts/self_heal.py", "--fix"]
        if os.environ.get("SKIP_VERSION_BUMP") != "1":
            cmd.append("--bump")
        if not run_cmd(cmd, root):
            print("   ❌ FAIL: Self-healing could not resolve all issues.")
            sys.exit(1)

    # 1. Hygiene (Strict or Auto-Clean)
    if args.auto_clean:
        print(f"{BOLD}🧹 AUTO-CLEAN (Deep Clean)...{RESET}")
        run_cmd([sys.executable, "-B", "scripts/clean_repo.py", "--clean", "--clean-generated"], root)

    try:
        # 2. Unit Tests
        print("🧪 RUNNING UNIT TESTS...")
        if not run_cmd([sys.executable, "-B", "-m", "unittest", "discover", "-s", "antigravity_harness/tests", "-p", "test*.py"], root):
            sys.exit(1)

        # 3. Pytest (Integration)
        print("🔥 RUNNING PYTEST...")
        # Institutional Gating: Skip distributed tests
        env = {"PYTHONPATH": "."}
        if not run_cmd([sys.executable, "-B", "-m", "pytest", "--import-mode=prepend", "-q", "-p", "no:cacheprovider", "-k", "not distributed"], root, env=env):
            sys.exit(1)

        # 5. Static Quality Gates
        if args.qa:
            print("🛡️ RUNNING STATIC QUALITY GATES (Institutional Mode)...")
            # Ruff
            print("   (Ruff Linting)")
            if not run_cmd([sys.executable, "-m", "ruff", "check", ".", "--no-cache"], root):
                sys.exit(1)
            # Mypy
            print("   (Mypy Type Check)")
            if not run_cmd([sys.executable, "-m", "mypy", ".", "--cache-dir=/tmp/.mypy_cache"], root):
                sys.exit(1)

        # Final Clean
        if args.auto_clean:
            print("✨ AUTO-CLEAN: Final sweep...")
            run_cmd([sys.executable, "-B", "scripts/clean_repo.py", "--clean", "--clean-generated"], root)

        # 4. Final Hygiene Check
        print("🔍 VERIFYING CLEANLINESS (Final Audit)...")
        if not run_cmd([sys.executable, "-B", "scripts/clean_repo.py", "--verify-strict"], root):
            msg = "Repo is dirty (Post-audit check failed)"
            log_event("HYGIENE", msg, "STARTUP")
            print(f"   ❌ FAIL: {msg}")
            success = False

    except KeyboardInterrupt:
        print("\n⚠️ ABORTED")
        sys.exit(130)

    print("--------------------------------")

    if success:
        print("✅ ALL SYSTEMS GO")
        sys.exit(0)
    else:
        print("🛑 PREFLIGHT FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
