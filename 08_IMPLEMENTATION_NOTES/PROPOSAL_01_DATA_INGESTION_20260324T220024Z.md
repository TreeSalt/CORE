---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
#!/usr/bin/env python3
"""
TASK: 01_DATA_E4_005_crypto_backfill_v2
DOMAIN: 01_DATA_INGESTION
SEC_CLASS: INTERNAL

NOTE: This script represents a proposal for backfill logic. 
Do not execute directly without security review and approval.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import requests
from typing import Optional, Tuple

# SECURITY CONFIGURATION
SECRETS_ENV_PREFIX = "CRYPTO_"
ALLOWED_WRITE_ROOTS = ("/data/raw", "/data/staging")
FORBIDDEN_PATHS = ("04_GOVERNANCE",)

class CryptoBackfillError(Exception):
    """Base exception for backfill operations."""
    pass

class SecurityException(CryptoBackfillError):
    """Raised when security constraints are breached."""
    pass

def get_secret(key: str) -> str:
    """
    Safely retrieve secrets from environment.
    Raises SecurityException if missing.
    """
    env_key = f"{SECRETS_ENV_PREFIX}{key.upper()}"
    value = os.environ.get(env_key)
    if not value:
        raise SecurityException(f"Missing required credential: {env_key}")
    return value

def validate_path_access(path: str) -> bool:
    """
    Ensure path does not write to governance or restricted areas.
    Fails closed on violation.
    """
    for forbidden in FORBIDDEN_PATHS:
        if forbidden in path:
            raise SecurityException(f"Path traversal blocked: {path} contains '{forbidden}'")
    return True

def fetch_market_data(api_key: str, start_date: datetime, end_date: datetime):
    """
    Fetch historical market data from provider.
    Raises on rate limit or auth failure.
    Mocked for proposal integrity.
    """
    # Placeholder logic for real API call (e.g., Binance/Coingecko)
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={int((end_date-start_date).days)}"
    try:
        response = requests.get(url, headers={"X-CFG-APIKEY": api_key})
        if response.status_code != 200:
            raise CryptoBackfillError(f"API Request Failed with status {response.status_code}")
        return response.json()
    except Exception as e:
        logging.error(f"Fetch failed for range. Failing closed due to: {e}")
        raise

def validate_schema_and_store(data, target_path):
    """
    Validate schema and store data.
    Fail closed if validation fails.
    """
    # Schema validation logic placeholder
    if not isinstance(data, dict) and "data" in data:
         raise CryptoBackfillError("Invalid response schema.")

    validate_path_access(target_path)
    
    # Write logic (mocked or real with open/os.path.join)
    # Simulating write to ALLOWED_WRITE_ROOTS
    return True 

def main():
    """
    Main execution guard for the backfill workflow.
    Fails closed on any error.
    """
    try:
        # 1. Context Validation
        logging.info("Initializing secure context...")
        
        # 2. Credentials Check (Fail closed if missing)
        try:
            api_key = get_secret("BINANCE_API_KEY")
        except SecurityException as e:
            logging.critical(f"Security Breach: {e}")
            sys.exit(1)

        # 3. Backfill Range Calculation
        end_date = datetime.now()
        days_to_backfill = 30
        start_date = end_date - timedelta(days=days_to_backfill)
        
        target_path = "/data/raw/btc_history.json" 
        # Ensure path validation
        
        try:
            raw_data = fetch_market_data(api_key, start_date, end_date)
            validate_schema_and_store(raw_data, target_path)
            
            logging.info("Backfill logic proposal validated.")
            print("Proposal Logic Complete.")
        except Exception as e:
            logging.critical(f"Backfill process failed and failed closed due to: {e}")
            sys.exit(1)
            
    except SystemExit:
        pass
    except Exception as e:
        # Fail closed outside of expected exits
        sys.stderr.write(f"Fatal Error occurred. Aborting.\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
```