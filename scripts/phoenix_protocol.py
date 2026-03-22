#!/usr/bin/env python3
"""
THE PHOENIX PROTOCOL (Wrapper)
--------------------
Verifies the Write-Ahead Log (WAL) resilience.
Delegates to mantis_core.phoenix.PhoenixProtocol.
"""

import os
import sys
from pathlib import Path

# Bootstrap path
sys.path.insert(0, os.getcwd())

try:
    from mantis_core.phoenix import PhoenixProtocol
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from mantis_core.phoenix import PhoenixProtocol

if __name__ == "__main__":
    protocol = PhoenixProtocol()

    if len(sys.argv) > 1 and sys.argv[1] == "run_victim":
        protocol.run_victim()
    else:
        # Pass this script's path so the survivor can spawn the victim via the same entry point
        protocol.run_survivor(str(Path(__file__).resolve()))
