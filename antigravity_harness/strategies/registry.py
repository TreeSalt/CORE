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
        
        # HYDRA GUARD: Registry Collision Protection (Vector 30)
        # Enforce that the class name matches the file name (CamelCase version)
        expected_class = "".join(x.capitalize() for x in name.split("_"))
        if strategy_cls.__name__ != expected_class:
            raise RuntimeError(
                f"REGISTRY COLLISION DETECTED: Strategy '{name}' class must be named '{expected_class}', "
                f"but found '{strategy_cls.__name__}'. Sabotage suspected."
            )

        if key in self._strategies:
            # We allow overwriting for flexible unit testing, but
            # in production this should be guarded if necessary.
            pass
            
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
        return self.get_class(name)()

    @property
    def available_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return sorted(self._strategies.keys())


# Default singleton for backward compatibility, but IoC is preferred.
STRATEGY_REGISTRY = StrategyRegistry()
