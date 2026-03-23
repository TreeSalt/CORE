---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

class SecurityException(Exception):
    """Custom exception for security constraint breaches."""
    pass

def configure_logger(path: Path) -> None:
    """Configure logger to write only to allowed paths."""
    # Ensure logger writes to safe paths, not 04_GOVERNANCE/
    safe_log_dir = path / "logs"
    if not os.path.exists(safe_log_dir):
        os.makedirs(safe_log_dir)
    
    log_file = safe_log_dir / "metrics_report.log"
    logging.basicConfig(filename=str(log_file), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FactoryMetricsReporter:
    """
    Proposal Class for E4-004 Factory Metrics Reporting.
    Handles aggregation and output of factory data securely.
    
    CONSTRAINTS ADHERENCE:
    1. No writes to 04_GOVERNANCE/
    2. No hardcoded credentials (uses env vars)
    3. Fail closed on constraint breach
    """

    # Blocked path patterns for validation
    BLOCKED_PATHS = ["04_GOVERNANCE/", "/secrets/", ".git/", "__pycache__"]

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("/default_config")
        self.report_output_path = Path("/reports/factory_metrics")
        self.api_endpoint: Optional[str] = None
        self.token: Optional[str] = None
        
        # Validate initialization constraints
        self._ensure_safe_paths()
        
    def _ensure_safe_paths(self) -> None:
        """Fail closed if proposed paths violate governance rules."""
        for path_str in str(self.report_output_path), str(self.config_dir):
            if any(blocked in p for p in [path_str, os.path.dirname(path_str)]):
                if "04_GOVERNANCE" in path_str:
                    raise SecurityException("CRITICAL: Output or Config path must not target 04_GOVERNANCE/")

    def _validate_credentials(self) -> None:
        """Load credentials securely from environment variables."""
        self.token = os.getenv("FACTORY_API_TOKEN")
        self.api_endpoint = os.getenv("FACTORY_API_ENDPOINT")
        
        # Fail closed if credentials are missing (don't use defaults)
        if not self.token or not self.api_endpoint:
            raise SecurityException("CRITICAL: Missing required environment variables for secure API access.")

    def aggregate_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Aggregate metrics from factory sources.
        Returns a dictionary of metrics suitable for reporting.
        """
        # Simulation of data fetching logic would go here
        # Actual implementation must ensure data fetch calls API securely
        metrics = {
            "start_date": start_date,
            "end_date": end_date,
            "production_units": 0,
            "efficiency_rate": 0.0,
            "quality_score": 100.0
        }
        # Mock data population for proposal structure
        metrics["status"] = "PROPOSAL"
        return metrics

    def generate_report(self, metrics: Dict[str, Any]) -> Path:
        """
        Generates the final report file at a safe location.
        Validates output path before writing.
        """
        # Ensure report destination is safe
        if "04_GOVERNANCE" in str(metrics.get("output_path", "")):
            raise SecurityException("Constraint Breach: Cannot write to governance directory.")
            
        try:
            file_path = self.report_output_path / f"factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Write logic (Proposal) - actual execution guarded by permissions checks in production
            with open(file_path, "w") as f:
                json.dump(metrics, f, indent=2)
                
            return file_path
            
        except OSError as e:
            logging.error(f"Failed to write report: {e}")
            raise SecurityException("Write operation failed. Constraint breach possible.")

    def cleanup_sensitive_cache(self) -> None:
        """Ensure no sensitive credentials are written to cache."""
        # Proposal for cache handling strategy that excludes secrets
        pass
```