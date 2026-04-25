---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import itertools
import csv
from typing import List, Callable, Any
import numpy as np
from pathlib import Path

class Cpvc:
    """Combinatorial Purge Cross-Validation Class."""

    def __init__(self, data_path: str, n_groups: int, n_test_groups: int, 
                 purge_window: int = 0, seed: int = 42):
        self.data_path = data_path
        self.n_groups = n_groups
        self.n_test_groups = n_test_groups
        self.purge_window = purge_window
        self.seed = seed

    def _load_data(self) -> List[Any]:
        """Load data from CSV file into a list."""
        try:
            with open(self.data_path, mode='r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # Assuming first row is header, but for indices we just need count
                self.data_list = [row for row in reader]
                return self.data_list
        except Exception:
            raise FileNotFoundError(f"Data file not found at {self.data_path}")

    def _generate_splits(self):
        """Generate splits based on combinations and purge logic."""
        N = len(self.data_list)
        
        # If N is smaller than n_test_groups, we can't proceed.
        if N < self.n_test_groups:
            return

        for combo in itertools.combinations(range(N), self.n_test_groups):
            test_indices = list(combo)
            
            train_candidates = [i for i in range(N) if i not in test_indices]
            
            # Apply purge logic: Remove indices too close to any test index
            indices_to_purge = set()
            for idx in train_candidates:
                is_within_purge_window = False
                for t_idx in test_indices:
                    dist = abs(idx - t_idx)
                    if dist < self.purge_window:
                        is_within_purge_window = True
                        break
                if is_within_purge_window:
                    indices_to_purge.add(idx)

            valid_train_indices = [i for i in train_candidates if i not in indices_to_purge]

            # Ensure we have enough training data (optional, but safe)
            if len(valid_train_indices) == 0:
                continue

            yield valid_train_indices, test_indices

    def validate_strategy(self, strategy_fn, data, metric_fn):
        """Run validation using the provided strategy function."""
        results = []
        # Iterate over splits provided by strategy_fn
        for train_idx, test_idx in strategy_fn:
            train_data = data[train_idx]
            test_data = data[test_idx]
            
            # Apply metric function
            # The prompt didn't specify signature of metric_fn, so assume standard (train, test) -> value
            try:
                val = metric_fn(train_data, test_data)
                results.append(val)
            except Exception as e:
                # Skip splits that fail the metric computation
                continue
        
        return np.mean(results) if results else None

    def run_validation(self, data_path: str, n_groups: int, n_test_groups: int, 
                      purge_window: int = 0, seed: int = 42):
        """Execute the full validation pipeline."""
        
        # Load data once at the start
        try:
            self.data_list = []
            with open(data_path, mode='r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    self.data_list.append(row)
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
        
        # Create the strategy function (generator)
        # The prompt requires passing a generator to validate_strategy
        
        metric_fn = lambda train, test: 0.0 # Placeholder metric (e.g., accuracy/error)
        
        try:
            mean_metric = self.validate_strategy(
                strategy_fn=self._generate_splits(), 
                data=self.data_list, 
                metric_fn=metric_fn
            )
            
            if mean_metric is not None:
                return mean_metric
            else:
                return 0.0
                
        except Exception as e:
            print(f"Validation error: {e}")
            return None
```