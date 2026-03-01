#!/usr/bin/env python3
"""
INFER UNIVERSE — TRADER_OPS Symbol Discovery Engine
===================================================
Derives the tradable universe by intersecting user intent,
seed profiles, and local cache metadata.
"""

import json
import sys
from pathlib import Path
from typing import Set

import yaml

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

def infer_universe(policy_path: Path, seed_path: Path) -> Set[str]:
    print("🔭 Inferring Universe...")
    
    universe: Set[str] = set()
    
    # 1. Start with Seed Profile allowlist (The physical ceiling)
    if seed_path.exists():
        with open(seed_path, "r") as f:
            seed = yaml.safe_load(f)
            seed_universe = set(seed.get("instrument_universe", {}).get("allowlist", []))
            print(f"   - Seed Ceiling: {seed_universe}")
    else:
        seed_universe = set()

    # 2. Extract Effective Policy Intent (The user goal)
    if policy_path.exists():
        with open(policy_path, "r") as f:
            policy = json.load(f)
            intent_universe = set(policy.get("universe", []))
            print(f"   - Intent Universe: {intent_universe}")
    else:
        intent_universe = set()

    # 3. Intersect (Only trade what is allowed AND intended)
    universe = intent_universe.intersection(seed_universe)
    
    # 4. Filter by availability (MOCK/MES check)
    # In Phase 2, we enforce MES as the truth anchor if specified.
    
    print(f"✅ Inferred Final Universe: {list(universe)}")
    return universe

def main():
    policy_path = REPO_ROOT / "profiles/users/alec/EFFECTIVE_POLICY.json"
    seed_path = REPO_ROOT / "profiles/seed_profile.yaml"
    
    universe = infer_universe(policy_path, seed_path)
    
    # Save to a temporary state file for next stage (Authorization)
    state_dir = REPO_ROOT / "state"
    state_dir.mkdir(exist_ok=True)
    with open(state_dir / "INFERRED_UNIVERSE.json", "w") as f:
        json.dump({"universe": list(universe)}, f)

if __name__ == "__main__":
    main()
