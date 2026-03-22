#!/usr/bin/env python3
"""
THE GREAT FILTER (CLI WRAPPER)
------------------------------
The Fiduciary Gatekeeper.
Wrapper for mantis_core.zip_verifier.ZipVerifier.
"""

import argparse
import sys
from pathlib import Path

# Implants the path to mantis_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from mantis_core.zip_verifier import ZipVerifier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sovereign Zip Verifier")
    parser.add_argument("--dist", default="dist", help="Path to dist directory (default: dist)")
    args = parser.parse_args()
    ZipVerifier(dist_dir=Path(args.dist)).run_all()
