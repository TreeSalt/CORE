#!/usr/bin/env python3
"""
THE GREAT FILTER (CLI WRAPPER)
------------------------------
The Fiduciary Gatekeeper.
Wrapper for antigravity_harness.zip_verifier.ZipVerifier.
"""

import sys
from pathlib import Path

# Implants the path to antigravity_harness
sys.path.insert(0, str(Path(__file__).parent.parent))

from antigravity_harness.zip_verifier import ZipVerifier

if __name__ == "__main__":
    ZipVerifier(dist_dir=Path("dist")).run_all()
