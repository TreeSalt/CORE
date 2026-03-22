#!/usr/bin/env python3
"""
CHAOS MONKEY (CLI WRAPPER)
--------------------------
The Saboteur of TRADER_OPS.
Wrapper for mantis_core.chaos_monkey.ChaosMonkey.
"""

import sys
from pathlib import Path
from typing import Callable, Dict

# Implants the path to mantis_core
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mantis_core.chaos_monkey import ChaosMonkey
except ImportError:
    # Fallback for when running from root
    from mantis_core.chaos_monkey import ChaosMonkey


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
        "v227": monkey.sabotage_volume,
        "v228": monkey.sabotage_slippage,
        "v240": monkey.sabotage_nan,
        "v231": monkey.sabotage_ledger_bloat,
        "v241": monkey.sabotage_timestamp_paradox,
        "v242": monkey.sabotage_homoglyph_strategy,
        "v243": monkey.sabotage_memory_bomb,
        "v244": monkey.sabotage_fd_exhaustion,
        "v245": monkey.sabotage_signal_tsunami,
        "v246": monkey.sabotage_symlink_poison,
        "v247": monkey.sabotage_immutability_paradox,
        "v248": monkey.sabotage_audit_race,
        "v249": monkey.sabotage_audit_resilience,
        "v250": monkey.sabotage_version_schism,
        "v263": monkey.sabotage_nan_midflight,
        "v264": monkey.sabotage_gate_bomb,
        "v265": monkey.sabotage_reports_heal_test,
        "v266": monkey.sabotage_stale_sidecar,
        "v267": monkey.sabotage_docs_version_drift,
        "v268": monkey.sabotage_drop_auditor_tamper,
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in dispatcher:
        dispatcher[cmd]()
    else:
        print(f"Unknown sabotage mode: {cmd}")


if __name__ == "__main__":
    main()
