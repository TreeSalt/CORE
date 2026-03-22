#!/usr/bin/env python3
"""
scripts/forge_evidence.py (Wrapper)
Phase 10.3: The Evidence Forge.
Delegates to mantis_core.evidence.EvidenceForge.
"""

import os
import sys
from pathlib import Path

# Bootstrap path
sys.path.insert(0, os.getcwd())

try:
    from mantis_core.evidence import EvidenceForge
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from mantis_core.evidence import EvidenceForge

if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    forge = EvidenceForge()
    forge.run()
