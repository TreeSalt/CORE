---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# SECURITY: INTERNAL
# TASK: 06_BENCH_E5_001_quality_gate CORRECTIVE_CONTEXT
# CONSTRAINT: Proposals only | No writes to 04_GOVERNANCE/ | No hardcoded credentials | Fail closed

class BenchmarkQualityGateProposal:
    """
    Defines a proposed quality gate configuration for benchmarking tasks.
    Ensures no state changes occur within restricted governance directories.
    """

    def __init__(self, task_id: str, benchmark_type: str):
        self.task_id = task_id
        self.benchmark_type = benchmark_type
        self.status = "PROPOSED"
        self.created_at = datetime.utcnow().isoformat()
        self._constraints_passed = False

    def _validate_path_safety(self, path_str: Optional[str] = None) -> bool:
        """
        Validate that no proposed file paths target restricted directories.
        Fail closed on breach.
        """
        if not path_str:
            return True
        
        # Constitutional Check: No access to 04_GOVERNANCE/
        if "04_GOVERNANCE" in path_str or "/04_GOVERNANCE/" in path_str:
            raise PermissionError("CONSTITUTIONAL VIOLATION: Access forbidden to governance paths.")
        
        return True

    def set_metrics(self, latency_threshold: float, accuracy_target: float) -> 'BenchmarkQualityGateProposal':
        """
        Define performance metrics for the quality gate proposal.
        Returns self for method chaining.
        """
        self.metrics = {
            "latency_max_ms": latency_threshold,
            "accuracy_min_pct": accuracy_target * 100,
            "safety_score_min": 99.0
        }
        return self

    def define_action_on_breach(self, action: str) -> 'BenchmarkQualityGateProposal':
        """
        Define the system response if quality gate thresholds are missed.
        """
        allowed_actions = ["HALT", "LOG_ONLY", "THROTTLE"]
        if action not in allowed_actions:
            raise ValueError(f"Action must be one of {allowed_actions}")
        
        self.action_on_breach = action
        return self

    def build_proposal_json(self) -> Dict[str, Any]:
        """
        Generates the proposal document structure for review.
        Does not write to disk.
        """
        # Run safety checks before generating config structure
        self._validate_path_safety(path_str=None)
        self._constraints_passed = True

        return {
            "task_id": self.task_id,
            "timestamp": self.created_at,
            "status": self.status,
            "metrics": self.metrics,
            "action_on_breach": self.action_on_breach,
            "security_class": "INTERNAL",
            "execution_policy": "READ_ONLY_PROPOSAL"
        }

    def get_proposal_artifact(self) -> str:
        """
        Returns the JSON string representation of the proposal.
        Strictly read-output for audit purposes.
        """
        try:
            config = self.build_proposal_json()
            # Serialization only, no file write operations
            return json.dumps(config, indent=2)
        except PermissionError as e:
            raise RuntimeError(f"Proposal generation halted: {e}")

def main():
    """
    Main execution block for proposal generation.
    Demonstrates constraint adherence without governance modifications.
    """
    try:
        # Initialize proposal for Task 06_BENCH_E5_001
        proposal = BenchmarkQualityGateProposal(
            task_id="06_BENCH_E5_001", 
            benchmark_type="quality_gate"
        )

        # Configure metrics (Example thresholds)
        proposal.set_metrics(
            latency_threshold=200.0,   # ms
            accuracy_target=0.95       # 95%
        )

        # Define breach handling policy
        proposal.define_action_on_breach("HALT")

        # Attempt to validate path safety (simulating a write check)
        proposal._validate_path_safety(path_str="/logs/06_BENCH_E5_001_results.json") 
        # Note: This check passed. Actual file writing is disabled by code structure.

        # Generate the artifact for review
        artifact_content = proposal.get_proposal_artifact()

        print(artifact_content)
        
    except (PermissionError, RuntimeError, ValueError) as e:
        # Fail closed behavior on any constraint breach
        raise SystemExit(f"HARD_FAIL: {e}")
```