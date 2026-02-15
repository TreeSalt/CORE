#!/usr/bin/env python3
"""
CHAOS MONKEY (CLI WRAPPER)
--------------------------
The Saboteur of TRADER_OPS.
Wrapper for antigravity_harness.chaos_monkey.ChaosMonkey.
"""

import sys
from pathlib import Path
from typing import Callable, Dict

# Implants the path to antigravity_harness
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from antigravity_harness.chaos_monkey import ChaosMonkey
except ImportError:
    # Fallback for when running from root
    from antigravity_harness.chaos_monkey import ChaosMonkey


def main():
    monkey = ChaosMonkey(dist_dir=Path("dist"))
    dispatcher: Dict[str, Callable] = {
        "binary": monkey.sabotage_binary,
        "ledger": monkey.sabotage_ledger,
        "evidence": monkey.sabotage_evidence,
        "manifest": monkey.sabotage_manifest,
        "metadata": monkey.sabotage_metadata,
        "engine": monkey.sabotage_engine,
        "basilisk": monkey.sabotage_basilisk,
        "echo": monkey.sabotage_echo,
        "chimera": monkey.sabotage_chimera,
        "kraken": monkey.sabotage_kraken,
        "mimic": monkey.sabotage_mimic,
        "legion": monkey.sabotage_legion,
        "gorgon": monkey.sabotage_gorgon,
        "all": monkey.run_all,
        "hydra": lambda: (monkey.sabotage_metadata(), monkey.sabotage_engine()),
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in dispatcher:
        dispatcher[cmd]()
    else:
        print(f"Unknown sabotage mode: {cmd}")


if __name__ == "__main__":
    main()
