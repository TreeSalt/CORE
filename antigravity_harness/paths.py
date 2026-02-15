import os
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


def ensure_dirs() -> None:
    """Create project directories only when explicitly requested (or CLI starts)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(CERT_DIR, exist_ok=True)
    os.makedirs(INTEL_DIR, exist_ok=True)
