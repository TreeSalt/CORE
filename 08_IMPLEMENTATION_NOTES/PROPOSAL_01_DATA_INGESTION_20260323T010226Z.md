---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

# Configure Logging to a secure local path (Avoiding /04_GOVERNANCE/)
def _setup_logger(log_dir: str = ".logs/ingestion"):
    """Configure logger to a non-governance writable directory."""
    os.makedirs(log_dir, exist_ok=True)
    log_path = Path(f"{os.getcwd()}/{log_dir}") / "crypto_backfill.log"
    
    # Ensure log directory does not match governance patterns
    assert "/04_GOVERNANCE/" not in str(log_path), "Log path cannot contain governance directories."
    
    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

class CryptoBackfillEngine:
    """
    Proprietary Proposal for Data Ingestion Task: 01_DATA_E4_005_crypto_backfill.
    
    SEC_CONSTRAINT_VIOLATION_CHECK:
      - No writes to /04_GOVERNANCE/
      - No hardcoded credentials
      - Fail closed on constraint breach
    """

    def __init__(self, task_id: str = "01_DATA_E4_005_crypto_backfill"):
        self.task_id = task_id
        logger = _setup_logger()
        logger.info(f"Initializing CryptoBackfillEngine for task: {task_id}")
        
        # Constraint Check: No hardcoded credentials. Enforcing Fail Closed behavior.
        self.api_key = os.getenv("CRYPTO_API_KEY")
        self.base_url = os.getenv("CRYPTO_DATA_BASE_URL", "https://api.example.com/data") # Placeholder, not real
        
        if not self.api_key:
            logger.critical("Constraint Breach: Missing API_KEY environment variable.")
            raise EnvironmentError("CREDENTIAL_MISSING_VIOLATION: No CRYPTO_API_KEY found. Fail Closed.")
        
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        # Define safe output directory (Non-governance)
        self.output_dir = Path.cwd() / "01_RAW_DATA" / "crypto_backfill"
        os.makedirs(self.output_dir, exist_ok=True)

    def _request_with_retry(self, url: str, method: str = "GET", max_retries: int = 3) -> Optional[requests.Response]:
        """
        Performs HTTP request with fail-closed logic. 
        If network fails or auth fails after retries, raise exception.
        """
        for attempt in range(max_retries):
            try:
                response = getattr(self.session, method)(url)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if self._is_auth_error(e):
                    logger.error(f"Auth failure on URL {url}. Fail Closed.")
                    return None
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {url}: {str(e)[:50]}")
        raise ConnectionError("Max retries exceeded. Connection unstable.")

    def _is_auth_error(self, exc: Exception) -> bool:
        """Check if exception is an authentication failure."""
        # Simple heuristic for auth errors to fail closed immediately
        if hasattr(exc, 'response') and exc.response.status_code == 401:
            return True
        return False

    def validate_source_availability(self) -> bool:
        """Validate source API connectivity before backfill."""
        test_url = f"{self.base_url}/status"
        try:
            response = self.session.get(test_url, timeout=5)
            if response.status_code == 200:
                logger.info("Source availability check passed.")
                return True
        except Exception:
            logger.error("Source validation failed. Backfill aborted (Fail Closed).")
            return False

    def fetch_historical_data(self, currency_pair: str = "BTC/USD", 
                              start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetches historical data. 
        Note: Start/end dates must be passed via arguments or config env vars (not hardcoded).
        """
        if not start_date:
            end_now = datetime.now() - timedelta(days=1) # Default 1 day back for safety
            start_now = end_now - timedelta(days=30) # Default 30 days window
            
            start_dt_str = start_now.strftime("%Y-%m-%d")
            end_dt_str = end_now.strftime("%Y-%m-%d")
            
            logger.info(f"Fetching data for {currency_pair} from {start_dt_str} to {end_dt_str}")
            
            url = f"{self.base_url}/v1/prices?pairs={currency_pair}&start={start_dt_str}&end={end_dt_str}"
            
            # Constraint: Do not write governance paths. Writing to self.output_dir (safe location)
            response = self._request_with_retry(url, "GET")
            
            if response is None:
                raise ConnectionError("API connection failed. Backfill halted.")

            data = response.json()
            
            # Save locally without overwriting sensitive or governance paths
            if 'data' in data:
                output_file = self.output_dir / f"{currency_pair}_{start_dt_str}_to_{end_dt_str}.json"
                
                with open(output_file, 'w') as f:
                    # Basic sanitization to ensure no secrets are written in raw text
                    safe_data = {k: v for k, v in data.items() if k not in ['api_key', 'secret']} 
                    json.dump(safe_data, f)
                
                logger.info(f"Data saved securely to {output_file}")
                return data['data']
            
            return []

    def validate_row_count(self, expected: int = 100, current: int = None) -> bool:
        """Simple validation for ingestion quality."""
        if not current:
            current = len(self._get_last_fetched_data())
        if current < expected:
            logger.warning(f"Low data volume. Current: {current}, Expected: {expected}")
            return False
        return True

    def run_task(self, currency_pair: str, duration_days: int = 30):
        """Main execution flow for the proposal task."""
        if not self.validate_source_availability():
            raise SystemExit("Source validation failed. Aborting.")

        start_date = datetime.now() - timedelta(days=duration_days)
        try:
            data = self.fetch_historical_data(currency_pair, start_date=start_date)
            # Constraint: No governance path usage in logic output
            assert "/04_GOVERNANCE/" not in str(Path.cwd()), "Runtime error: Governance path detected."
            if not self.validate_row_count(expected=100):
                raise ValueError("Validation failed. Incomplete data.")
            logger.info(f"Task {self.task_id} completed successfully with {len(data)} records.")
        except Exception as e:
            logger.error(f"Task failure: {e}")
            # Fail closed behavior on critical errors
            sys.exit(1)

# Main Execution Guard (Only executed if run directly)
if __name__ == "__main__":
    engine = CryptoBackfillEngine(task_id="01_DATA_E4_005_crypto_backfill")
    # Example execution, safe defaults applied
    try:
        engine.run_task(currency_pair="ETH/USD", duration_days=30)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
```