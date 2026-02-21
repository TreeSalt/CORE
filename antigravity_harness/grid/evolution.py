import random
from typing import Any, Dict

class StrategyEvolver:
    """
    Item 25: Self-Evolving Opt-Matrix.
    Mutation logic for strategy parameters across generations.
    """
    def mutate(self, params: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        new_params = params.copy()
        for k, v in new_params.items():
            if isinstance(v, (int, float)) and random.random() < mutation_rate:
                change = 1.0 + (random.uniform(-0.2, 0.2))
                new_params[k] = type(v)(v * change)
        return new_params
