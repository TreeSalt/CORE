---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, Callable
from datetime import datetime

# ==============================================================================
# SECURITY & GOVERNANCE CONSTRAINT CHECKER (FAIL CLOSED)
# ==============================================================================
class BenchmarkConstraintGuard:
    """
    Enforces security constraints on the benchmark environment.
    Raises exceptions if constraints are violated (Fail Closed).
    """

    FORBIDDEN_PATHS = {'04_GOVERNANCE/'}
    ALLOWED_LOG_PATH_PREFIXES = ['05_BENCHMARKING', 'logs/', './']

    @classmethod
    def validate_env(cls) -> bool:
        current_path = Path.cwd()
        str_path = str(current_path)
        
        for forbidden in cls.FORBIDDEN_PATHS:
            if forbidden in str_path:
                raise RuntimeError(f"Constraint Breach: Current directory path {str_path} contains forbidden segment '{forbidden}'")
        
        # Ensure no write attempts to forbidden paths later by validating config
        config_check = os.getenv('CONFIG_DIR') or '.'
        if '04_GOVERNANCE' in config_check:
            raise RuntimeError(f"Constraint Breach: CONFIG_DIR is pointing to forbidden path.")

        return True

    @classmethod
    def get_secure_creds(cls) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieves credentials from environment variables only.
        No hardcoded values permitted.
        """
        api_key = os.getenv('API_KEY', default=None)
        secret_token = os.getenv('SECRET_TOKEN', default=None)
        
        if api_key is None or secret_token is None:
            # Return empty/None for test simulation, do not hardcode fallbacks
            return (None, None)
            
        return (api_key, secret_token)

# ==============================================================================
# OVERNIGHT RANGE TRAP TEST DEFINITION
# ==============================================================================
class OvernightRangeTrapTest:
    """
    Proposal for an overnight benchmarking test to monitor metric ranges.
    Detects 'range traps' where values drift out of expected bounds over time.
    """
    
    def __init__(self, 
                 target_metric_name: str, 
                 min_bound: float, 
                 max_bound: float, 
                 check_interval_seconds: int,
                 log_dir: Optional[str] = None):
        
        if '04_GOVERNANCE' in (log_dir or ''):
             raise ValueError("Log directory cannot point to 04_GOVERNANCE/")

        self.metric_name = target_metric_name
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.check_interval = check_interval_seconds
        self.log_path = f"{log_dir or './bench_logs'}"
        
        # Setup logging outside of forbidden paths
        try:
            os.makedirs(self.log_path, exist_ok=True)
        except PermissionError:
            raise PermissionError(f"Cannot create log directory in {self.log_path}. Check permissions.")

        self._start_time: Optional[float] = None
        self._violations: list = []

    def run_check(self, current_value: float) -> bool:
        """
        Performs the range trap check for a single value.
        Returns True if within bounds, False otherwise.
        """
        is_valid = self.min_bound <= current_value <= self.max_bound
        status = "VALID" if is_valid else "TRAP_DETECTED"
        
        log_msg = f"[{datetime.now()}] Metric: {self.metric_name} | Value: {current_value:.4f} | Status: {status}"
        
        # Log to file (no console spam for security/overhead)
        try:
            if status == "TRAP_DETECTED":
                self._violations.append(log_msg)
                logging.warning(log_msg)
            else:
                logging.debug(log_msg)
        except Exception as e:
            # Fail closed on logging issues too, but don't crash the whole suite
            raise RuntimeError(f"Logging failure (Constraint Check): {e}")
            
        return is_valid

    def run_overnight_simulation(self, sample_count: int = 100) -> dict:
        """
        Simulates an overnight check cycle.
        In production, this would wrap with actual data fetching.
        
        Constraint Note: This script does NOT write to 04_GOVERNANCE/.
        """
        
        if not BenchmarkConstraintGuard.validate_env():
            raise PermissionError("Environment validation failed.")
            
        creds = BenchmarkConstraintGuard.get_secure_creds()
        if creds[0]: # Optional usage check, but we don't use them here directly to avoid exposure
             pass

        self._start_time = time.time()
        logging.basicConfig(level=logging.INFO)
        
        violations_count = 0
        for i in range(sample_count):
            # Generate synthetic data or fetch real data (using secure config if needed)
            # Here we simulate values to test the logic without external dependencies
            simulated_value = self.min_bound + (i % 10) * 0.5 
            # Introduce some randomness for realism (or trap injection)
            import random
            variance = random.uniform(0, 2.0)
            
            if random.random() < 0.1: # 10% chance of trap injection for testing detection
                simulated_value += abs(variance) * 5
            
            self.run_check(simulated_value)
            
            # Simulate sleep without blocking too hard in a proposal context
            # time.sleep(self.check_interval / 60) 

        elapsed = time.time() - self._start_time
        return {
            "metric": self.metric_name,
            "bounds": (self.min_bound, self.max_bound),
            "samples_check": sample_count,
            "violations_detected": len(self._violations),
            "runtime_seconds": round(elapsed, 2)
        }

# ==============================================================================
# EXECUTION PROPOSAL ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    # This block executes only if the proposal is accepted and deployed.
    # It validates constraints immediately (Fail Closed).
    
    try:
        # Validate current environment path security first
        BenchmarkConstraintGuard.validate_env()
        
        # Initialize Test Instance with secure defaults
        test_config = OvernightRangeTrapTest(
            target_metric_name="sys_cpu_load",
            min_bound=0.0,
            max_bound=0.95,
            check_interval_seconds=60,
            log_dir="./logs/bench_E6" # Ensures no write to 04_GOVERNANCE/
        )
        
        # Run the overnight range trap test logic (Simulation Mode for Proposal)
        # In production: use data from external APIs using creds from env vars
        report = test_config.run_overnight_simulation(sample_count=100)
        
        print(f"Test Complete. Violations: {report['violations_detected']}")
        
    except PermissionError as e:
        # Fail Closed behavior on constraint breach
        sys.stderr.write(f"FATAL: Constraint Breach Detected - {e}\n")
        sys.exit(1)
    except RuntimeError as e:
        sys.stderr.write(f"FATAL: Critical Error - {e}\n")
        sys.exit(1)