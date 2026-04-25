---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from typing import Callable, Any
import csv


class ReplayResults:
    """Container for replay execution results."""
    
    def __init__(self):
        self.results = []
        self.success_count = 0
        self.failure_count = 0
    
    def add_result(self, result: dict, success: bool = True):
        """Add a single test case result."""
        self.results.append(result)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def get_results(self) -> list:
        """Return all collected results."""
        return self.results
    
    def summary(self) -> dict:
        """Return summary statistics."""
        total = len(self.results)
        return {
            'total': total,
            'success': self.success_count,
            'failure': self.failure_count
        }


class ReplayHarness:
    """Harness for replaying test cases from CSV through a pipeline."""
    
    def __init__(self, csv_path: str, pipeline_factory: Callable[[], Any]):
        self.csv_path = csv_path
        self.pipeline_factory = pipeline_factory
    
    def _load_csv_data(self) -> list:
        """Load test cases from CSV file."""
        data = []
        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        return data
    
    def _execute_pipeline(self, pipeline: Any, test_case: dict) -> tuple:
        """Execute a single test case through the pipeline."""
        try:
            result = pipeline(test_case) if callable(pipeline) else pipeline.run(test_case)
            return result, True
        except Exception as e:
            return {'error': str(e)}, False
    
    def replay(self) -> ReplayResults:
        """Replay all test cases from CSV without deterministic seeding."""
        results = ReplayResults()
        pipeline = self.pipeline_factory()
        data = self._load_csv_data()
        
        for case in data:
            output, success = self._execute_pipeline(pipeline, case)
            results.add_result(output, success)
        
        return results
    
    def replay_with_seed(self, seed: int) -> ReplayResults:
        """Replay all test cases with deterministic random seeding."""
        import random
        random.seed(seed)
        return self.replay()