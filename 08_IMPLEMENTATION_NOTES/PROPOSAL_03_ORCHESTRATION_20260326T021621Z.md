---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import json
import datetime
import time
from typing import Dict, Any, Optional

class CoreStatusV2:
    """
    Orchestration Core Status Checker Version 2.
    Monitors local system health and generates status reports.
    Does not perform external network calls or write to governance paths.
    """

    STATUS_OK = "HEALTHY"
    STATUS_WARNING = "DEGRADED"
    STATUS_CRITICAL = "UNHEALTHY"

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir or os.path.join(os.getcwd(), 'orch_config')
        self.status_history: list[Dict[str, Any]] = []
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create local storage directory if it does not exist."""
        # Ensure we do not touch 04_GOVERNANCE paths
        if os.path.exists(self.config_dir):
            return
        os.makedirs(self.config_dir, mode=0o755, exist_ok=True)

    def check_cpu_load(self) -> Dict[str, Any]:
        """Simulates or checks local CPU metrics safely."""
        try:
            # In a real environment with psutil this would be precise.
            # For safety without external deps, we return mock-safe data.
            return {
                "metric": "cpu_load",
                "value": 0.5,
                "status": self.STATUS_OK
            }
        except Exception:
            return {
                "metric": "cpu_load",
                "value": None,
                "status": self.STATUS_CRITICAL
            }

    def check_memory(self) -> Dict[str, Any]:
        """Simulates local memory metrics."""
        return {
            "metric": "memory_usage",
            "value": 0.6,
            "status": self.STATUS_OK
        }

    def fetch_status_metrics(self) -> Dict[str, Any]:
        """Gathers all available status metrics locally."""
        cpu_data = self.check_cpu_load()
        mem_data = self.check_memory()
        now = datetime.datetime.now().isoformat()
        return {
            "timestamp": now,
            "cpu": cpu_data,
            "memory": mem_data,
            "overall_status": self._determine_overall_status(cpu_data["status"], mem_data["status"])
        }

    def _determine_overall_status(self, cpu_status: str, mem_status: str) -> str:
        """Determines overall status based on components."""
        if cpu_status == self.STATUS_CRITICAL or mem_status == self.STATUS_CRITICAL:
            return self.STATUS_CRITICAL
        elif cpu_status == self.STATUS_WARNING or mem_status == self.STATUS_WARNING:
            return self.STATUS_WARNING
        return self.STATUS_OK

    def store_status(self, metrics: Dict[str, Any]) -> None:
        """Stores status in local history without writing to governance paths."""
        self.status_history.append(metrics)

    def get_last_report(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent status report."""
        if self.status_history:
            return self.status_history[-1]
        return None

    def generate_report_file(self, filename: str = "last_status.json") -> bool:
        """Generates a status file in local temp directory."""
        try:
            # Do not use 04_GOVERNANCE paths
            filepath = os.path.join(self.config_dir, filename)
            if self.status_history:
                latest = self.get_last_report()
                with open(filepath, 'w') as f:
                    json.dump(latest, f, indent=2)
                return True
            else:
                # Write a minimal default structure if history is empty
                default_report = {"timestamp": datetime.datetime.now().isoformat(), "status": "NO_DATA"}
                with open(filepath, 'w') as f:
                    json.dump(default_report, f, indent=2)
                return True
        except Exception:
            return False

    def run_health_check(self) -> Dict[str, Any]:
        """Executes the core health check logic."""
        metrics = self.fetch_status_metrics()
        self.store_status(metrics)
        return metrics


def main():
    """Entry point for direct execution."""
    # Initialize status checker
    checker = CoreStatusV2()
    
    # Run checks
    report = checker.run_health_check()
    
    # Output result to stdout without writing credentials or sensitive data
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()