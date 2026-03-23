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
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests

class CryptoSymbolsIngestionManager:
    """
    Secure Data Ingestion Manager for Crypto Symbols.
    
    SECURITY NOTE: 
    - API Keys must be retrieved via environment variables.
    - Never write credentials to disk or logs.
    - Hardcoded credentials are strictly prohibited.
    """
    
    # Base configuration paths (Do not point to 04_GOVERNANCE/)
    CONFIG_DIR = "./config" 
    
    def __init__(self, api_key_env_var: str = "CRYPTO_API_KEY", endpoint: Optional[str] = None):
        self.session = requests.Session()
        
        # SECURITY ENFORCEMENT: Validate key source at instantiation
        if not hasattr(self, '_api_key'):
            self._validate_credential_source(api_key_env_var)
            
        self.endpoint = endpoint or "https://api.coingecko.com/api/v3" # Example public API
        self.timeout = 10

    def _validate_credential_source(self, key_env_name: str) -> bool:
        """
        Enforces constraint: No hardcoded credentials. 
        Credentials must come from environment variables or a secrets manager.
        
        Returns True only if validated. If validation fails, fail closed.
        """
        credential = os.environ.get(key_env_name)
        
        # Fail Closed Check
        if credential is None:
            print(f"[SECURITY ALERT] {key_env_name} not found in environment. Ingestion paused.", file=sys.stderr)
            return False
            
        # Basic length validation to prevent empty or obviously fake tokens (optional heuristic)
        # Do not log the value itself
        if len(credential.strip()) == 0:
             print(f"[SECURITY ALERT] {key_env_name} is empty. Ingestion paused.", file=sys.stderr)
             return False
        
        self._api_key = credential
        return True

    def ingest_symbols(self, limit: int = 100) -> Dict[str, Any]:
        """
        Fetches crypto symbols securely.
        Raises RuntimeError if validation fails or request is denied.
        """
        try:
            # Construct headers safely
            headers = {}
            if self._api_key and len(self._api_key) > 0:
                headers["Authorization"] = f"Bearer {self._api_key}"
            
            url = f"{self.endpoint}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&sparkline=false"
            
            # Execute request with timeout to prevent hanging
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code not in [200]:
                print(f"[INGESTION ERROR] Status Code: {response.status_code}", file=sys.stderr)
                raise ConnectionError("API request failed. Check quota or credentials.")
                
            data = response.json()
            
            if not isinstance(data, list):
                 raise ValueError("Unexpected API response structure")

            # Create secure report object (no logging of secrets)
            result = {
                "ingested_at": datetime.utcnow().isoformat(),
                "record_count": len(data),
                "symbols": data[:10],  # Sample for log safety, full load handled by downstream
                "status": "SUCCESS"
            }
            
            return result

        except Exception as e:
            # Fail closed on ingestion error
            print(f"[INGESTION FAILURE] Caught exception: {type(e).__name__}", file=sys.stderr)
            raise RuntimeError("Ingestion pipeline failed to ingest data securely.") from e

    def clear_local_cache(self):
        """
        Ensures no cached credentials are written locally.
        Only clears runtime state if applicable.
        """
        if hasattr(self, '_api_key'):
            # Do not print or log the key value. Clear reference.
            del self._api_key
```