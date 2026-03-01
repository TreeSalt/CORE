#!/usr/bin/env python3
"""
INTAKE COMPILE — TRADER_OPS Intent Specification Compiler
=========================================================
Validates and compiles INTENT_SPEC.yaml into internal security policies.
Governs symbols, exposure, and risk boundaries.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

# Add repo root for imports
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.append(str(REPO_ROOT))

# ─── Schema Models (Pydantic) ────────────────────────────────────────────────

class IntentItem(BaseModel):
    strategy_id: str
    symbols: List[str]
    max_exposure_usd: float = Field(ge=0)
    max_contracts: int = Field(default=1, ge=1)
    risk_tier: str = Field(default="BALANCED")  # CONSERVATIVE, BALANCED, AGGRESSIVE
    allow_overnight: bool = False

class GlobalLimits(BaseModel):
    total_max_drawdown_pct: float = Field(default=10.0, ge=0, le=100)
    daily_loss_limit_usd: float = Field(default=500.0, ge=0)
    emergency_delever_button: bool = False

class IntentSpec(BaseModel):
    version: str
    user: str
    intents: List[IntentItem]
    global_limits: Optional[GlobalLimits] = Field(default_factory=GlobalLimits)

# ─── Compiler Logic ──────────────────────────────────────────────────────────

def compile_spec(spec_path: Path, out_path: Optional[Path] = None) -> bool:
    print(f"🛠️  Compiling IntentSpec: {spec_path.relative_to(REPO_ROOT)}")

    if not spec_path.exists():
        print(f"❌ Error: Spec file not found at {spec_path}")
        return False

    try:
        with open(spec_path, "r") as f:
            raw_data = yaml.safe_load(f)
        
        # Validate against Pydantic model
        spec = IntentSpec(**raw_data)
        
        # Flatten into Effective Policy
        effective_policy = {
            "version": spec.version,
            "user": spec.user,
            "compiled_at": str(Path("/dev/stdin").stat().st_mtime), # Placeholder or real time
            "universe": list(set([s for i in spec.intents for s in i.symbols])),
            "strategy_bounds": {i.strategy_id: i.model_dump() for i in spec.intents},
            "global_limits": spec.global_limits.model_dump() if spec.global_limits else {}
        }

        # Save if requested
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(effective_policy, f, indent=2)
            print(f"✅ Compiled Effective Policy saved to: {out_path.relative_to(REPO_ROOT)}")

        return True

    except ValidationError as e:
        print(f"❌ Schema Validation Failed:\n{e}")
        return False
    except Exception as e:
        print(f"❌ Compiler Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="TRADER_OPS IntentSpec Compiler")
    parser.add_argument("--spec", type=str, required=True, help="Path to INTENT_SPEC.yaml")
    parser.add_argument("--out", type=str, help="Path to save compiled EFFECTIVE_POLICY.json")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    out_path = Path(args.out).resolve() if args.out else None

    success = compile_spec(spec_path, out_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
