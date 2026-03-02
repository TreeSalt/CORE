#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Task 1: Institutional Cleanliness (Bytecode Prevention)
sys.dont_write_bytecode = True


def clean_repo(clean: bool = False, clean_generated: bool = False, verify_strict: bool = False, deep_audit: bool = False) -> int:  # noqa: PLR0912, PLR0915
    root = Path(__file__).parent.parent.resolve()

    is_verify_only = verify_strict or deep_audit or (not clean and not clean_generated)
    mode = "Auditing" if deep_audit else ("Verifying" if is_verify_only else "Cleaning")
    print(f"🧹 {mode} repo root: {root}")

    forbidden_artifacts = []
    generated_outputs = []

    # 1. Strict Detection List
    strict_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "*.log",
        "tmp",
        "data_cache",
        "MANIFEST.json",
    ]

    venv_root = root / ".venv"
    for pat in strict_patterns:
        if "*" in pat:
            for path in root.rglob(pat):
                if not path.is_relative_to(venv_root):
                    forbidden_artifacts.append(path)
        else:
            for path in root.rglob(pat):
                if not path.is_relative_to(venv_root):
                    forbidden_artifacts.append(path)

    # 2. Generated Outputs
    output_patterns = ["reports", "reports_old", "reports_production", "dist"]
    for pat in output_patterns:
        p = root / pat
        if p.exists():
            generated_outputs.append(p)

    # 3. Deep Audit (Institutional Hygiene)
    untracked_garbage = []
    if deep_audit:
        try:
            # List ALL untracked/ignored files
            status = subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=root, text=True
            ).strip()
            if status:
                for line in status.splitlines():
                    p = root / line
                    # Filter out allowed data/cache items or authorized roots? 
                    # For now, flag ALL untracked in source tree
                    if line.startswith("antigravity_harness/") or line.startswith("scripts/"):
                        untracked_garbage.append(p)
        except subprocess.CalledProcessError:
            pass

    # Report Findings
    all_artifacts = forbidden_artifacts + (generated_outputs if clean_generated else []) + untracked_garbage

    if all_artifacts:
        print("🔍 Artifact Report:")
        for p in forbidden_artifacts:
            print(f"   [FORBIDDEN] {p.relative_to(root)}")
        for p in generated_outputs:
            if clean_generated:
                print(f"   [GENERATED] {p.relative_to(root)}")
            else:
                print(f"   [STAYING]   {p.relative_to(root)} (use --clean-generated to remove)")
        for p in untracked_garbage:
             status = "[UNTRACKED]"
             if p.suffix in (".py", ".sh", ".so", ".exe", ".bin"):
                 status = "[RISKY_UNTRACKED]"
             print(f"   {status:13} {p.relative_to(root)}")

    # Execution logic
    if is_verify_only:
        if forbidden_artifacts:
            print("❌ VERIFY-STRICT: Forbidden artifacts exist.")
            return 1
        if deep_audit and untracked_garbage:
            print("❌ DEEP-AUDIT: Unauthorized untracked files detected in source tree.")
            return 1
        print(f"✅ {mode}: Repo is clean.")
        return 0

    # Cleaning logic
    deleted_count = 0

    # Task 2 compliance: reports/ certification/ sweeps/ should be cleanable?
    # Always clean forbidden artifacts if --clean passed
    if clean:
        for path in forbidden_artifacts:
            if not path.exists():
                continue
            print(f"   Removing {path.relative_to(root)}")
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            deleted_count += 1

    # Clean generated outputs ONLY if --clean-generated passed
    if clean_generated:
        for path in generated_outputs:
            if not path.exists():
                continue
            print(f"   Removing {path.relative_to(root)}")
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            deleted_count += 1

    if deleted_count > 0:
        print(f"✨ Clean complete ({deleted_count} items removed).")
    else:
        print("✨ Nothing to clean.")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Release Hygiene")
    parser.add_argument("--clean", action="store_true", help="Delete forbidden cache artifacts")
    parser.add_argument("--clean-generated", action="store_true", help="Delete generated outputs (reports/, dist/)")
    parser.add_argument("--clean-reports", action="store_true", help="Legacy alias for --clean-generated")
    parser.add_argument("--verify-strict", action="store_true", help="Check only, fail if forbidden exist")
    parser.add_argument("--deep-audit", action="store_true", help="Comprehensive scan for ANY untracked files in source")
    args = parser.parse_args()

    # Handle legacy flags
    if args.clean_reports:
        args.clean_generated = True

    sys.exit(clean_repo(args.clean, args.clean_generated, args.verify_strict, args.deep_audit))
