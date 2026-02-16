import os
import sys
from pathlib import Path

# DETERMINISTIC REPO LAYOUT
# File: 02_STRATEGY_ENGINE/antigravity_harness/paths.py
# Parents:
# 0 -> antigravity_harness
# 1 -> 02_STRATEGY_ENGINE [PROJECT ROOT]

REPO_ROOT = Path(__file__).resolve().parents[1]

# Core Directories
DATA_DIR = REPO_ROOT / "05_DATA_CACHE"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
REPORT_DIR = REPO_ROOT / "reports"
CERT_DIR = REPORT_DIR / "certification"
INTEL_DIR = REPO_ROOT / "intelligence"


def _safe_mkdir(path: Path) -> None:
    """Create a directory, auto-healing if a file is blocking the path.

    Handles Hydra V249-class attacks where a file replaces a directory.
    """
    if path.exists() and not path.is_dir():
        # Self-heal: a file is blocking the directory path
        print(f"⚕️  [HEAL] Removing blocking file at {path} (expected directory)", file=sys.stderr)
        path.unlink()
    os.makedirs(path, exist_ok=True)


def ensure_dirs() -> None:
    """Create project directories only when explicitly requested (or CLI starts).

    Self-heals any path corruption (e.g., file blocking a directory).
    """
    for d in (DATA_DIR, SNAPSHOT_DIR, REPORT_DIR, CERT_DIR, INTEL_DIR):
        _safe_mkdir(d)

