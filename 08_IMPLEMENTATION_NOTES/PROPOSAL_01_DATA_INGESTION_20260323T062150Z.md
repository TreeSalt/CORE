---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import logging
import requests
from typing import List, Dict, Optional
from time import sleep

# Configuration for secure ingestion
class SecureCryptoIngestion:
    """
    Implements fail-closed logic for cryptocurrency symbol ingestion.
    Strictly uses documented CoinGecko API endpoints.
    Reads credentials from environment variables only (No hardcoded keys).
    """
    
    # Documented Endpoint: /api/v3/coins/list
    ENDPOINT = "/api/v3/coins/list" 
    BASE_URL = "https://api.coingecko.com"

    def __init__(self):
        self.session = requests.Session()
        self.setup_logging()
        
        # Attempt to load key securely from env, never defaulting to 'demo' in code
        self.api_key = os.getenv("COINGECKO_API_KEY", None) 

    def setup_logging(self):
        """Setup logger to avoid internal write access."""
        _LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        self.logger = logging.getLogger("CryptoIngestion")
        # Ensure handler is added once (prevent spam) if not present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            self.logger.addHandler(handler)

    def _get_headers(self):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'CryptoSymbolService-v2.0'
        }
        # Only add auth header if key exists in environment
        if self.api_key:
            headers['x-cg-demo-api-key'] = self.api_key 
        return headers

    def fetch_symbols(self) -> List[Dict[str, str]]:
        """
        Fetches symbols securely.
        Returns empty list on failure (Fail Closed).
        """
        url = f"{self.BASE_URL}{self.ENDPOINT}"
        timeout = 15
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=timeout)
            
            if response.status_code == 200:
                raw_data = response.json()
                # Ensure structure is safe (Fail closed on malformed data)
                if isinstance(raw_data, list):
                    return [{"symbol": item.get("symbol"), "name": item.get("id")} for item in raw_data]
            elif response.status_code == 401: # Unauthorized or Key Error
                self.logger.warning("API key missing or invalid.")
                return [] 
            elif response.status_code == 429: # Rate Limit
                self.logger.warning("Rate limit hit. Retrying after 60s cooldown.")
                sleep(60)
                return self.fetch_symbols()
            else:
                self.logger.error(f"API Request Failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            # Fail closed on network issues
            self.logger.critical(f"Network failure during ingestion: {e}")
        except ValueError as e:
            self.logger.critical(f"Invalid response format from API: {e}")
            
        return []

    def run(self) -> List[Dict[str, str]]:
        """Entry point to fetch symbols."""
        return self.fetch_symbols()

if __name__ == "__main__":
    # Safe execution block if running as script (Proposals only)
    ingester = SecureCryptoIngestion()
    symbols = ingester.run()
    print(f"Ingested {len(symbols)} symbols safely.")
```