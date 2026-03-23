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
import json
import requests

def ingest_crypto_symbols():
    """
    Proposed Corrective Context for TASK: 01_DATA_E4_003_crypto_symbols
    Fixes: 
      1. Removes 'cryptography' hallucinated import (replaced with standard API client).
      2. Enforces Fail-Closed behavior on missing environment credentials.
      3. Ensures no hardcoded credentials are present in source code.
    """
    
    # SECURITY CHECK: Retrieve API key from secure environment variable
    # Do not attempt to fallback to hardcoded values
    api_key = os.environ.get("DATA_INGESTION_API_KEY")
    
    if not api_key:
        print("[SECURITY] FAILED: CREDENTIALS NOT FOUND IN ENVIRONMENT.")
        print("[ACTION] Closing process per Fail-Closed policy.")
        sys.exit(1)
    
    # Define secure headers with API key
    headers = {
        "Accept": "application/json",
        "X-API-KEY": api_key
    }
    
    # Use standard, reliable HTTP client (requests)
    # Note: 'cryptography' is not required for public API symbol ingestion.
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process symbols safely without cryptography overhead
            symbol_list = [item['symbol'] for item in data]
            
            print(f"[SUCCESS] Ingested {len(symbol_list)} crypto symbols.")
            return symbol_list
            
        else:
            print(f"[ERROR] HTTP Status Code: {response.status_code}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError as e:
        print(f"[NETWORK] Connection failed: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"[PARSE] JSON Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_crypto_symbols()
```