#!/usr/bin/env python3
"""
Strategy Governance Tool (v4.5.81)
Manages the STRATEGY_REGISTRY.json: initialization, registration, promotion, and verification.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
STRATEGY_ROOT = REPO_ROOT / "antigravity_harness" / "strategies"
REGISTRY_FILE = STRATEGY_ROOT / "STRATEGY_REGISTRY.json"

TIERS = ["quarantine", "lab", "certified"]

def compute_merkle_root(strategy_path: Path) -> str:
    """Computes a stable hash (Merkle Root) of the strategy folder."""
    if not strategy_path.exists():
        return ""
    
    files = sorted([f for f in strategy_path.rglob("*") if f.is_file() and "__pycache__" not in f.parts])
    hashes = []
    for f in files:
        rel_path = f.relative_to(strategy_path).as_posix()
        file_hash = hashlib.sha256(f.read_bytes()).hexdigest()
        hashes.append(f"{rel_path}:{file_hash}")
        
    manifest_blob = "\n".join(hashes).encode("utf-8")
    return hashlib.sha256(manifest_blob).hexdigest()

def init_registry():
    """Seed the registry with default tier policies."""
    data = {
        "schema_version": "1.0.0",
        "tier_policy": {
            "research": ["quarantine", "lab", "certified"],
            "paper": ["lab", "certified"],
            "live": ["certified"]
        },
        "strategies": {}
    }
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Initialized {REGISTRY_FILE}")

def register_strategy(name: str, tier: str):
    """Register (or re-hash) a strategy in its current tier folder."""
    if tier not in TIERS:
        print(f"❌ Error: Invalid tier '{tier}'. Must be one of {TIERS}")
        sys.exit(1)
        
    strategy_path = STRATEGY_ROOT / tier / name
    if not strategy_path.exists():
        print(f"❌ Error: Strategy folder not found at {strategy_path}")
        sys.exit(1)
        
    merkle_root = compute_merkle_root(strategy_path)
    
    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)
        
    registry["strategies"][name] = {
        "tier": tier,
        "merkle_root_sha256": merkle_root
    }
    
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)
        
    print(f"✅ Registered '{name}' ({tier})")
    print(f"   Hash: {merkle_root}")

def promote_strategy(name: str, target_tier: str):
    """Move a strategy to a higher tier and update registry."""
    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)
        
    if name not in registry["strategies"]:
        print(f"❌ Error: Strategy '{name}' is not registered.")
        sys.exit(1)
        
    current_tier = registry["strategies"][name]["tier"]
    if TIERS.index(target_tier) <= TIERS.index(current_tier):
        print(f"❌ Error: Target tier '{target_tier}' must be higher than current '{current_tier}'")
        sys.exit(1)

    src = STRATEGY_ROOT / current_tier / name
    dst = STRATEGY_ROOT / target_tier / name
    
    print(f"🚀 Promoting '{name}': {current_tier} -> {target_tier}")
    
    if dst.exists():
        print(f"⚠️ Warning: Target folder {dst} exists. Overwriting.")
        shutil.rmtree(dst)
        
    shutil.move(src, dst)
    
    # Re-register
    register_strategy(name, target_tier)

def verify_all():
    """Audit the integrity of all registered strategies."""
    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)
        
    all_ok = True
    for name, meta in registry["strategies"].items():
        tier = meta["tier"]
        strategy_path = STRATEGY_ROOT / tier / name
        actual_hash = compute_merkle_root(strategy_path)
        
        if actual_hash == meta["merkle_root_sha256"]:
            print(f"  [OK] {name:30} ({tier})")
        else:
            print(f"  [!!] {name:30} ({tier}) - HASH_MISMATCH!")
            all_ok = False
            
    if not all_ok:
        print("\n❌ Governance Audit FAILED.")
        sys.exit(1)
    else:
        print("\n✅ Governance Audit PASSED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy Governance Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("init")
    
    reg_parser = subparsers.add_parser("register")
    reg_parser.add_argument("name")
    reg_parser.add_argument("--tier", default="quarantine")
    
    prom_parser = subparsers.add_parser("promote")
    prom_parser.add_argument("name")
    prom_parser.add_argument("tier")
    
    subparsers.add_parser("verify")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_registry()
    elif args.command == "register":
        register_strategy(args.name, args.tier)
    elif args.command == "promote":
        promote_strategy(args.name, args.tier)
    elif args.command == "verify":
        verify_all()
    else:
        parser.print_help()
