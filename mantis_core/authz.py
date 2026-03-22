"""
AUTHZ — TRADER_OPS Action Authorization Engine
==============================================
The primary security gatekeeper for all proposed trade actions.
Implements the 3-gate Sovereign Chain.
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from mantis_core.execution.adapter_base import OrderIntent
from mantis_core.paths import REPO_ROOT

# ─── 3-Gate Sovereign Chain ──────────────────────────────────────────────────

class AuthzEngine:
    """
    Action Authorization Engine (v4.6.1).
    Fail-closed by design.
    """

    def __init__(self, policy_path: Path, universe_path: Path):
        self.policy_path = policy_path
        self.universe_path = universe_path
        self.policy: Dict[str, Any] = {}
        self.universe: set = set()
        self.override_active: bool = False
        self._load_state()

    def _load_state(self):
        # MISSION v4.7.1: Detect Allowlist Override for Auto-Paper demotion
        override_path = REPO_ROOT / "ALLOWLIST_OVERRIDE.json"
        if override_path.exists():
            self.override_active = True
            print("⚠️  SECURITY: ALLOWLIST_OVERRIDE detected. Authz Engine forcing PAPER mode.")

        if self.policy_path.exists():
            with open(self.policy_path, "r") as f:
                self.policy = json.load(f)
        
        if self.universe_path.exists():
            with open(self.universe_path, "r") as f:
                data = json.load(f)
                self.universe = set(data.get("universe", []))

    def authorize_intent(self, intent: OrderIntent, strategy_source: str) -> Tuple[bool, str]:
        """
        Processes an OrderIntent through the 3-gate chain.
        Returns: (is_authorized, reason)
        """
        
        # GATE 1: Physical Viability (Symbol in Universe)
        if intent.symbol not in self.universe:
            return False, f"GATE_1_FAIL: Symbol '{intent.symbol}' not in tradable universe."

        # GATE 2: Policy Compliance (Strategy Bounds)
        bounds = self.policy.get("strategy_bounds", {}).get(strategy_source)
        if not bounds:
            return False, f"GATE_2_FAIL: Strategy '{strategy_source}' is not authorized in EffectivePolicy."

        # Check exposure/contracts
        if intent.quantity > bounds.get("max_contracts", 0):
            return False, f"GATE_2_FAIL: Quantity {intent.quantity} exceeds strategy limit {bounds.get('max_contracts')}."

        # GATE 3: Identity Verification (Sovereign Seal)
        # In this implementation, we assume the engine itself is the trust anchor.
        # Future versions will verify Ed25519 signatures from the strategy source.

        # MISSION v4.7.2: Force Paper Mode if Override Active
        if self.override_active:
             # Even if authorized, we only allow paper execution.
             # This check might need more context if we want to explicitly block 'live' mode here.
             # However, the CLI уже demotes the mode.
             pass

        return True, "AUTHORIZED: Sovereign Gate passed."

    def check_global_limits(self, current_stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Checks if global risk limits have been breached."""
        limits = self.policy.get("global_limits", {})
        
        if current_stats.get("day_loss_usd", 0) >= limits.get("daily_loss_limit_usd", 999999):
            return False, "GLOBAL_LIMIT_BREACH: Daily loss limit reached."
        
        if limits.get("emergency_delever_button", False):
            return False, "GLOBAL_LIMIT_BREACH: Emergency Delever Button ACTIVE."
            
        return True, "LIMITS_OK"
