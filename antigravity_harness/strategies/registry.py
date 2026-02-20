from __future__ import annotations

from typing import Dict, List, Type

from antigravity_harness.strategies.base import Strategy


class StrategyRegistry:
    """
    The Cartographer of Alphas.
    Explicitly manages the mapping of names to strategy classes,
    enabling Inversion of Control and quarantine rules.
    """

import hashlib
import json
from pathlib import Path

# Paths
REGISTRY_FILE = Path(__file__).parent / "STRATEGY_REGISTRY.json"
STRATEGY_ROOT = Path(__file__).parent

TIER_MAP = {
    "quarantine": 0,
    "lab": 1,
    "certified": 2
}

class StrategyRegistry:
    """
    The Cartographer of Alphas.
    Explicitly manages the mapping of names to strategy classes,
    enabling Inversion of Control and quarantine rules.
    """

    def __init__(self):
        self._strategies: Dict[str, Type[Strategy]] = {}
        self._registry_data = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if not REGISTRY_FILE.exists():
            return {"strategies": {}, "tier_policy": {}}
        try:
            with open(REGISTRY_FILE) as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"REGISTRY CORRUPTION: Could not load STRATEGY_REGISTRY.json: {e}")

    def register(self, name: str, strategy_cls: Type[Strategy]) -> None:
        """Register a strategy with a unique name."""
        key = name.strip().lower()
        
        # HYDRA GUARD: Registry Collision Protection (Vector 30)
        # Enforce that the class name matches the file name (CamelCase version)
        expected_class = "".join(x.capitalize() for x in name.split("_"))
        if strategy_cls.__name__ != expected_class:
            raise RuntimeError(
                f"REGISTRY COLLISION DETECTED: Strategy '{name}' class must be named '{expected_class}', "
                f"but found '{strategy_cls.__name__}'. Sabotage suspected."
            )
            
        # HYDRA GUARD: Exec Poison (Vector 87) & Thread Hijack (Vector 104) & Builtin Tamper (Vector 117)
        # Static analysis scan for forbidden dynamic execution and hijacking signatures
        try:
            import inspect  # noqa: PLC0415
            source = inspect.getsource(strategy_cls)
            forbidden = [
                "eval(", "exec(", "compile(",  # V87
                "threading", "multiprocessing", "subprocess", # V104
                "__builtins__", "globals()", "locals()" # V117
            ]
            if any(f in source for f in forbidden):
                raise RuntimeError(
                    f"SECURITY VIOLATION: Strategy '{name}' uses forbidden signatures: "
                    f"{[f for f in forbidden if f in source]}. Quarantine required."
                )
        except Exception as e:
            if "SECURITY VIOLATION" in str(e):
                raise
            
        self._strategies[key] = strategy_cls

    def get_class(self, name: str) -> Type[Strategy]:
        """Retrieve the strategy class by name."""
        key = name.strip().lower()
        if key not in self._strategies:
            raise KeyError(f"Sovereign Error: Unknown strategy '{name}'. Available: {self.available_strategies}")
        return self._strategies[key]

    def instantiate(self, name: str) -> Strategy:
        """Retrieve and instantiate a strategy by name."""
        # Runtime Governance Check
        self.verify_strategy_allowed(name)
        return self.get_class(name)()

    @property
    def available_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return sorted(self._strategies.keys())

    def verify_strategy_allowed(self, name: str, mode: str = "research") -> None:
        """
        GOVERNANCE GATE: Verifies strategy is registered, verified, and allowed in mode.
        """
        if name not in self._registry_data.get("strategies", {}):
            raise RuntimeError(f"GOV-001 UNREGISTERED: Strategy '{name}' not found in STRATEGY_REGISTRY.json.")
            
        strat_meta = self._registry_data["strategies"][name]
        tier = strat_meta.get("tier", "quarantine")
        
        # 1. Tier Enforcement
        allowed_tiers = self._registry_data.get("tier_policy", {}).get(mode, [])
        if tier not in allowed_tiers:
             raise RuntimeError(f"GOV-003 TIER_BLOCKED: Strategy '{name}' ({tier}) not allowed in mode '{mode}'. Allowed: {allowed_tiers}")

        # 2. Hash Verification (If strict mode or explicit verification requested)
        # We enforce Merkle Root verification for ALL modes to prevent tampering.
        # This is "FAIL CLOSED".
        expected_hash = strat_meta.get("merkle_root_sha256", "")
        if not expected_hash or expected_hash == "PENDING_HASH":
             raise RuntimeError(f"GOV-002 HASH_MISSING: Strategy '{name}' has no active hash in registry.")
             
        actual_hash = self.compute_strategy_hash(name)
        if actual_hash != expected_hash:
             raise RuntimeError(
                 f"GOV-002 HASH_MISMATCH: Strategy '{name}' integrity check failed.\n"
                 f"   Expected: {expected_hash}\n"
                 f"   Actual:   {actual_hash}\n"
                 f"   Tampering suspected."
             )

    def compute_strategy_hash(self, name: str) -> str:
        """Computes Merkle root of the strategy artifacts."""
        if name not in self._registry_data["strategies"]:
            return ""
            
        tier = self._registry_data["strategies"][name]["tier"]
        # Expected path: strategies/{tier}/{name}/
        strategy_path = STRATEGY_ROOT / tier / name
        
        if not strategy_path.exists():
            return "MISSING_ARTIFACT"
            
        # 1. List files recursively, sorted
        files = sorted([f for f in strategy_path.rglob("*") if f.is_file() and "__pycache__" not in f.parts])
        
        hashes = []
        for f in files:
            # Relative path for stability
            rel_path = f.relative_to(strategy_path).as_posix()
            file_hash = hashlib.sha256(f.read_bytes()).hexdigest()
            hashes.append(f"{rel_path}:{file_hash}")
            
        # Merkle Root
        manifest_blob = "\n".join(hashes).encode("utf-8")
        return hashlib.sha256(manifest_blob).hexdigest()

STRATEGY_REGISTRY = StrategyRegistry()
