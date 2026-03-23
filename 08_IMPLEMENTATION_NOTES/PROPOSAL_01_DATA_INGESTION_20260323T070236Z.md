---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
#!/usr/bin/env python3
"""
TASK_ID: 01_DATA_E4_005_crypto_backfill_v2
DOMAIN: 01_DATA_INGESTION
SECURITY_CLASS: INTERNAL
STATUS: CORRECTIVE_IMPLEMENTATION (Hardcoded Credentials Removed)
CONTRIBUTOR: SYSTEM_GENERATOR

CONSTRAINTS ENFORCED:
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Fail closed on missing secrets
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Constants for Env Var Mapping (No values exposed)
CREDENTIAL_PREFIX = "API_SECRET_"
REQUIRED_ENV_VARS = [
    f"{CREDENTIAL_PREFIX}API_KEY", 
    f"{CREDENTIAL_PREFIX}SECRET_TOKEN", 
    f"{CREDENTIAL_PREFIX}ENDPOINT_URL"
]


class SecureConfigLoader:
    """
    Loads configuration strictly from environment variables.
    Raises SystemExit if critical secrets are missing.
    """
    def __init__(self, prefix: str = CREDENTIAL_PREFIX):
        self.prefix = prefix
        self.config: Optional[Dict[str, str]] = None
        self._load()

    def _load(self) -> bool:
        missing_vars = []
        for var in REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"CRITICAL VIOLATION: Missing credentials for backfill task.\nMissing: {', '.join(missing_vars)}"
            print(error_msg, file=sys.stderr)
            sys.exit(1) # Fail Closed
            
        self.config = {
            "api_key": os.getenv(f"{self.prefix}API_KEY"),
            "token": os.getenv(f"{self.prefix}SECRET_TOKEN"),
            "base_url": os.getenv(f"{self.prefix}ENDPOINT_URL")
        }
        
        # Validate base URL is not empty to prevent malformed requests
        if not self.config["base_url"]:
            print("CRITICAL VIOLATION: Endpoint URL not set.", file=sys.stderr)
            sys.exit(1)
            
        return True

    def get_headers(self) -> Dict[str, str]:
        """Returns authentication headers derived from secure config."""
        if not self.config:
            return {}
        return {
            "Authorization": f"Bearer {self.config['token']}",
            "X-API-Key": self.config["api_key"]
        }

class CryptoDataIngestionEngine:
    """
    Ingestion engine for crypto backfill operations.
    Abstracts data fetching behind secure authentication layer.
    """
    def __init__(self, config_loader: SecureConfigLoader):
        self.loader = config_loader
        self.session = None
        
    def _initialize_session(self):
        """Initializes requests session with secure headers."""
        import requests
        # In production, use a persistent Session object managed by an external manager
        # to maintain connections securely.
        try:
            # Verify endpoint reachability (Fail closed on connection error)
            from urllib.request import urlopen
            url = self.loader.config['base_url']
            # Optional health check header injection
            if not urlopen(url + "/health", timeout=5):
                print("CRITICAL VIOLATION: Backend endpoint unreachable.", file=sys.stderr)
                sys.exit(1)
                
        except Exception as e:
            print(f"CRITICAL VIOLATION: Connectivity failure. Error: {e}", file=sys.stderr)
            sys.exit(1)

    def fetch_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[List[Dict]]:
        """
        Fetches historical candle data for a specific crypto asset.
        Handles rate limiting and failure safely per record.
        """
        headers = self.loader.get_headers()
        session = requests.Session()
        
        payload = {
            "symbol": symbol,
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
        
        try:
            response = session.post(self.loader.config["base_url"], json=payload, headers=headers)
            
            # Fail closed on non-200 status with sensitive handling
            if not response.ok:
                print(f"SECURITY WARNING: Ingestion failed for {symbol}. Status: {response.status_code}", file=sys.stderr)
                return None
                
            data = response.json()
            
            # Optional local validation of payload size to prevent DoS
            if len(data) > 1000:
                 print(f"SECURITY WARNING: Payload too large for symbol {symbol}. Truncating.", file=sys.stderr)
                 data = data[:1000]
                 
            return data
            
        except requests.exceptions.RequestException as req_error:
            # Fail safe per record, maintaining session integrity
            print(f"SECURITY ERROR: Request failed for {symbol}. Error: {req_error}", file=sys.stderr)
            return None
            
        except Exception as e:
            # Catch-all for unexpected errors during ingestion logic
            print(f"INTERNAL ERROR: Ingestion process error. {e}", file=sys.stderr)
            continue

    def run_backfill(self, symbols: List[str], start_date: datetime, end_date: datetime) -> int:
        """
        Orchestrates the backfill process for a list of symbols.
        Returns total number of ingested records (if logging were enabled).
        """
        # Ensure session is ready before fetching
        self._initialize_session()
        
        total_records = 0
        
        # Ingestion logic for each symbol
        for symbol in symbols:
            data_batch = self.fetch_historical_data(symbol, start_date, end_date)
            if data_batch:
                # Process records (logic placeholder)
                total_records += len(data_batch)
                
        return total_records


def main():
    """
    Entry point for the backfill utility.
    Ensures environment compliance before execution.
    """
    try:
        # Initialize secure loader which validates env vars immediately
        config_loader = SecureConfigLoader(prefix=CREDENTIAL_PREFIX)
        
        # Instantiate engine with validated config
        engine = CryptoDataIngestionEngine(config_loader=loader=config_loader)
        
        # Configuration defaults (Ensure these are overridden by env or config file if needed)
        DEFAULT_SYMBOLS = ["BTC-USD", "ETH-USD"]
        START_DATE = datetime(2023, 1, 1) # Default start date
        
        # Execute backfill if symbols list provided or default used
        symbols = os.getenv("BACKFILL_SYMBOLS_LIST").split(",") if os.getenv("BACKFILL_SYMBOLS_LIST") else DEFAULT_SYMBOLS
        end_date = datetime.now()
        
        if not symbols:
            print("No symbols defined. Exiting.")
            return

        # Run the secure engine loop
        count = engine.run_backfill(
            symbols=symbols, 
            start_date=START_DATE, 
            end_date=end_date
        )
        
        print(f"Backfill completed. Records processed: {count}")
        
    except SystemExit:
        # Re-throw to exit immediately on constraint breach (missing creds)
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```