from __future__ import annotations

from typing import Dict, List, Type

from antigravity_harness.strategies.base import Strategy


class StrategyRegistry:
    """
    The Cartographer of Alphas.
    Explicitly manages the mapping of names to strategy classes,
    enabling Inversion of Control and quarantine rules.
    """

    def __init__(self):
        self._strategies: Dict[str, Type[Strategy]] = {}

    def register(self, name: str, strategy_cls: Type[Strategy]) -> None:
        """Register a strategy with a unique name."""
        key = name.strip().lower()
        if key in self._strategies:
            # We allow overwriting for flexible unit testing, but
            # in production this should be guarded if necessary.
            pass
        self._strategies[key] = strategy_cls

    def get_class(self, name: str) -> Type[Strategy]:
        """Retrieve the strategy class by name."""
        key = name.strip().lower()
        if key not in self._strategies:
            raise KeyError(f"Sovereign Error: Unknown strategy '{name}'. Available: {self.available_strategies}")
        return self._strategies[key]

    def instantiate(self, name: str) -> Strategy:
        """Retrieve and instantiate a strategy by name."""
        return self.get_class(name)()

    @property
    def available_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return sorted(self._strategies.keys())


# Default singleton for backward compatibility, but IoC is preferred.
STRATEGY_REGISTRY = StrategyRegistry()
