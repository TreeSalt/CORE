---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from dataclasses import dataclass
from typing import Optional, Any
import csv
import random


@dataclass
class ReplayResults:
    """Container for replay validation results."""
    success: bool
    records_processed: int
    errors: list[str]
    metrics: dict[str, float]

    def __init__(self):
        self.success = True
        self.records_processed = 0
        self.errors = []
        self.metrics = {}


class ReplayHarness:
    """Harness for replaying validation scenarios from CSV data."""

    def __init__(self, csv_path: str, pipeline_factory: callable):
        self.csv_path = csv_path
        self.pipeline_factory = pipeline_factory
        self._data_cache: Optional[list[dict[str, Any]]] = None

    def _load_csv(self) -> list[dict[str, Any]]:
        """Load data from CSV file into a list of dictionaries."""
        records = []
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        return records

    def _execute_pipeline(self, record: dict[str, Any], seed: Optional[int] = None) -> tuple[bool, list[float]]:
        """Execute the pipeline factory with a single record."""
        if seed is not None:
            random.seed(seed)
        pipeline = self.pipeline_factory()
        result = pipeline.process(record)
        metrics = getattr(result, 'metrics', [])
        return bool(result.success), [float(m) for m in metrics]

    def _aggregate_results(self, individual_results: list[tuple[bool, list[float]]]) -> ReplayResults:
        """Aggregate individual record results into final ReplayResults."""
        r = ReplayResults()
        r.records_processed = len(individual_results)
        
        successes = [r_result for r_result, _ in individual_results]
        r.success = all(successes)
        
        error_count = sum(1 for s, _ in individual_results if not s)
        if error_count > 0:
            for i, (success, _) in enumerate(individual_results):
                if not success:
                    r.errors.append(f"Record {i}: processing failed")
        
        all_metrics = []
        for _, metrics in individual_results:
            all_metrics.extend(metrics)
        
        if all_metrics:
            r.metrics['mean'] = sum(all_metrics) / len(all_metrics)
            r.metrics['min'] = min(all_metrics)
            r.metrics['max'] = max(all_metrics)
            r.metrics['count'] = len(all_metrics)
        
        return r

    def replay(self) -> ReplayResults:
        """Replay all records from the CSV through the pipeline."""
        if self._data_cache is None:
            self._data_cache = self._load_csv()
        
        individual_results = []
        for i, record in enumerate(self._data_cache):
            success, metrics = self._execute_pipeline(record)
            individual_results.append((success, metrics))
        
        return self._aggregate_results(individual_results)

    def replay_with_seed(self, seed: int) -> ReplayResults:
        """Replay all records with a deterministic seed for reproducibility."""
        random.seed(seed)
        
        if self._data_cache is None:
            self._data_cache = self._load_csv()
        
        individual_results = []
        for i, record in enumerate(self._data_cache):
            success, metrics = self._execute_pipeline(record, seed=seed + i)
            individual_results.append((success, metrics))
        
        return self._aggregate_results(individual_results)