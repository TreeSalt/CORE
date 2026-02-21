from typing import Any, Dict, List

from antigravity_harness.grid.evolution import StrategyEvolver
from antigravity_harness.grid.matrix import EvaluationMatrix


class GridManager:
    """
    Item 23/25: Grid Manager.
    Orchestrates the evolution and evaluation of strategies across the grid.
    """
    def __init__(self, state_path=None, n_jobs: int = 1):
        self.state_path = state_path
        self.n_jobs = n_jobs
        self.matrix = EvaluationMatrix()
        self.evolver = StrategyEvolver()

    def execute_batch(self, func, tasks):
        """Standard batch execution for the grid."""
        try:
            from joblib import Parallel, delayed  # noqa: PLC0415
            return Parallel(n_jobs=self.n_jobs)(delayed(func)(*t) for t in tasks)
        except ImportError:
            # Fallback to sequential
            return [func(*t) for t in tasks]

    def evolve_and_evaluate(self, strategy_id: str, base_params: Dict[str, Any], generations: int = 5) -> List[Dict[str, Any]]:
        current_params = base_params
        all_results = []
        for _gen in range(generations):
            # Evaluate current gen
            results = self.matrix.run_matrix(strategy_id, [current_params])
            all_results.extend(results)
            # Evolve for next gen
            current_params = self.evolver.mutate(current_params)
        return all_results
