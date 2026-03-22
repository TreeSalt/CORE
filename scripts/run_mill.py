#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mantis_core.mill import Alchemist, Reaper, persist_sovereign_strategy  # type: ignore[import]


def main():
    pool = ["RSI_14", "SMA_200", "ADX_14", "MACD_12_26"]
    alchemist = Alchemist(pool)
    reaper = Reaper(min_sharpe=1.2, max_dd=0.25)

    print("🏭 Mill Protocol Initiated...")
    candidates = alchemist.transmutate(50)
    print(f"🧪 Alchemist generated {len(candidates)} candidates.")

    best = reaper.judge(candidates)

    if best:
        dist = Path("dist")
        dist.mkdir(exist_ok=True)
        path = dist / "sovereign_strategy_mill_v1.json"
        persist_sovereign_strategy(best, path)
    else:
        print("☠️ No Survivors. The Mill grinds on.")


if __name__ == "__main__":
    main()
