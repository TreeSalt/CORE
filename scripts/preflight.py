#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Task 1: Institutional Cleanliness (Bytecode Prevention)
sys.dont_write_bytecode = True


def run_cmd(cmd: str, cwd: Path, env: Optional[dict] = None) -> bool:
    print(f"🚀 RUN: {cmd}")
    try:
        # Task 3: Disable bytecode creation if requested (by using -B or environment)
        # We ensure PYTHONDONTWRITEBYTECODE is set for the subprocess
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        result = subprocess.run(cmd, shell=True, check=False, cwd=cwd, env=current_env)
        if result.returncode == 0:
            print("   ✅ PASS")
            return True
        else:
            print(f"   ❌ FAIL (Exit Code: {result.returncode})")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def main() -> None:  # noqa: PLR0912
    parser = argparse.ArgumentParser(description="Antigravity Preflight")
    parser.add_argument("--auto-clean", action="store_true", help="Clean repo before verification")
    parser.add_argument("--qa", action="store_true", help="Run static quality gates (ruff + mypy)")
    args = parser.parse_args()

    # Task 3: Global bytecode suppression
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    print("🛫 ANTIGRAVITY PREFLIGHT CHECK (Institutional Mode)")
    print("--------------------------------")

    root = Path(__file__).parent.parent.resolve()
    success = True

    # 1. Hygiene (Strict or Auto-Clean)
    if args.auto_clean:
        print("🧹 AUTO-CLEAN ENABLED")
        if not run_cmd("python3 -B scripts/clean_repo.py --clean --clean-generated", root):
            sys.exit(1)

    # Always Verify Strict (No Mutation allowed here)
    print("🔍 VERIFYING CLEANLINESS (Pre-Test)...")
    if not run_cmd("python3 -B scripts/clean_repo.py --verify-strict", root):
        if not args.auto_clean:
            print("   💡 Hint: Run with --auto-clean to fix.")
        sys.exit(1)

    try:
        # 2. Unit Tests
        # Task 3: use python3 -B for extra safety
        print("🧪 RUNNING UNIT TESTS...")
        if not run_cmd("python3 -B -m unittest discover -s antigravity_harness/tests -p 'test*.py'", root):
            sys.exit(1)

        # 3. Pytest (Integration)
        print("🔥 RUNNING PYTEST...")
        # Institutional Gating: Skip distributed tests to prevent semaphore leaks
        if not run_cmd("PYTHONPATH=. python3 -B -m pytest --import-mode=prepend -q -p no:cacheprovider -k 'not distributed'", root):
            sys.exit(1)

        # 5. Static Quality Gates (Task 5)
        if args.qa:
            print("🛡️ RUNNING STATIC QUALITY GATES (Institutional Mode)...")
            # Ruff
            print("   (Ruff Linting)")
            if not run_cmd("python3 -m ruff check . --no-cache", root):
                sys.exit(1)
            # Mypy
            print("   (Mypy Type Check)")
            if not run_cmd("python3 -m mypy . --cache-dir=/tmp/.mypy_cache", root):
                sys.exit(1)

        # Final Clean (if auto-clean requested)
        if args.auto_clean:
            print("✨ AUTO-CLEAN: Final sweep...")
            run_cmd("python3 -B scripts/clean_repo.py --clean --clean-generated", root)

        # 4. Final Hygiene Check (Task 3: Post-Test Verification)
        print("🔍 VERIFYING CLEANLINESS (Final Audit)...")
        if not run_cmd("python3 -B scripts/clean_repo.py --verify-strict", root):
            print("   ❌ FAIL: Repo is dirty.")
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
