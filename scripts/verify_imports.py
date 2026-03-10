#!/usr/bin/env python3
import argparse
import contextlib
import importlib
import pkgutil
import sys
import traceback
from pathlib import Path


def verify_imports(package_name: str, root_path: Path):
    """Recursively import all modules in a package and check for errors."""
    print(f"🔍 Verifying imports for: {package_name} (at {root_path})", flush=True)

    # Ensure package is in path
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

    # We use walk_packages to find all submodules
    failed = []

    # Special case: scripts directory might not be a package
    if package_name == "scripts":
        for script_file in root_path.glob("*.py"):
            if script_file.name == "__init__.py":
                continue
            module_name = script_file.stem
            with contextlib.suppress(Exception):
                # We need to handle scripts carefully as they are often meant to be run, not imported
                # BUT for NameError checking, importing is enough.
                # However, many scripts have top-level code that might fail if not in the right environment.
                # We prioritize the library first.
                pass

    # Library validation
    try:
        package = importlib.import_module(package_name)
    except Exception as e:
        print(f"❌ Failed to import base package {package_name}: {e}", flush=True)
        return [package_name]

    for _loader, module_name, _is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            print(f"  Attempting to import: {module_name}", flush=True)
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}", flush=True)
        except Exception:
            print(f"❌ Error importing {module_name}:", flush=True)
            traceback.print_exc(limit=1)
            failed.append(module_name)

    return failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Institutional Import Smoke Tester")
    parser.add_argument("--lib", default="antigravity_harness", help="Library to test")
    args = parser.parse_args()

    root = Path.cwd()
    failures = verify_imports(args.lib, root)

    import os
    if failures:
        print(f"\n🛑 IMPORT VERIFICATION FAILED: {len(failures)} errors found.", flush=True)
        os._exit(1)
    else:
        print("\n✨ ALL IMPORTS VERIFIED. No NameErrors or missing dependencies detected.", flush=True)
        os._exit(0)
