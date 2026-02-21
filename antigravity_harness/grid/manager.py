from typing import Any, Dict, List
from antigravity_harness.grid.matrix import EvaluationMatrix
from antigravity_harness.grid.evolution import StrategyEvolver

class GridManager:
    """
    Item 23/25: Grid Manager.
    Orchestrates the evolution and evaluation of strategies across the grid.
    """
    def __init__(self):
        self.matrix = EvaluationMatrix()
        self.evolver = StrategyEvolver()

    def evolve_and_evaluate(self, strategy_id: str, base_params: Dict[str, Any], generations: int = 5) -> List[Dict[str, Any]]:
        current_params = base_params
        all_results = []
        for gen in range(generations):
            # Evaluate current gen
            results = self.matrix.run_matrix(strategy_id, [current_params])
            all_results.extend(results)
            # Evolve for next gen
            current_params = self.evolver.mutate(current_params)
        return all_results
