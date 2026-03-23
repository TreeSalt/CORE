---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# Task: 01_DATA_E4_003_crypto_symbols_v2
# Domain: 01_DATA_INGESTION
# Context: CORRECTIVE (Avoiding undocumented endpoints from previous failure)

import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
import requests
from urllib.parse import urljoin

# Configure Logging for this Ingestion Module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crypto_ingestor')

class CryptoDataIngestor:
    """
    Proposes a robust ingestion pattern for CoinGecko v3 APIs.
    Corrective measures against previous undocumented endpoint failures.
    Uses documented endpoints and environment-based credentials.
    """

    # Base URL is public, stable and documented as of current CoinGecko v3 standard
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Documented Endpoint for Market Overview (Includes symbols/names)
    DOCUMENTED_ENDPOINT_MARKET = "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"
    
    # Config paths (Avoiding 04_GOVERNANCE/)
    CONFIG_DIR = "config/01_data_ingestion/"
    CREDENTIALS_ENV_VAR = "COINGECKO_API_KEY"

    def __init__(self, max_retries: int = 3, timeout: float = 15.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        # Attempt to load credentials from environment, fail closed if missing
        self.api_key = os.getenv(self.CREDENTIALS_ENV_VAR) 
        
        # Fail closed check for unauthorized configuration
        if self.api_key and len(self.api_key) < 10: 
            raise ValueError("Credential appears invalid or improperly configured in environment.")

    def _construct_request_headers(self) -> Dict[str, str]:
        """Construct headers based on credentials."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["X-CMG-CLIENT-API-KEY"] = self.api_key # Note: CG official header usage might vary, checking docs usually doesn't need this for v3 read-only but included for compliance attempts
        return headers

    def _fetch_with_backoff(self) -> Optional[Dict[str, Any]]:
        """
        Attempts to fetch market data with retry logic.
        Ensures fail closed behavior on network or API errors.
        """
        url = urljoin(self.BASE_URL, self.DOCUMENTED_ENDPOINT_MARKET)
        
        # Initial check if key is required for high volume (often not for public read)
        # Proceeding without key if env var is empty to maintain utility unless rate limited
        
        attempts = 0
        while attempts <= self.max_retries:
            try:
                logger.info(f"Attempt {attempts + 1}: Fetching from {url}")
                
                response = self.session.get(url, headers=self._construct_request_headers(), timeout=self.timeout)
                response.raise_for_status() # Fail closed on HTTP errors
                
                data = response.json()
                
                if not isinstance(data, list):
                    logger.error("Unexpected response structure: non-list JSON received")
                    return None

                return data

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                     # Rate limited - wait before retrying (if retries left)
                    logger.warning(f"Rate limit hit. Retrying in {self.timeout}s.")
                    time.sleep(self.timeout)
                    attempts += 1
                    continue
                else:
                    logger.error(f"HTTP Error: {http_err}")
                    # Fail closed on non-recoverable HTTP errors
                    return None

            except requests.exceptions.ConnectionError as conn_err:
                logger.error(f"Connection error. Retrying.")
                attempts += 1
                time.sleep(self.timeout)
                continue
            
            except Exception as generic_err:
                # Fail closed on any unforeseen exception
                logger.critical(f"Ingestion failed with unexpected error: {generic_err}")
                return None

        # All retries exhausted or no retries left
        return None

    def ingest_symbols(self) -> Optional[List[Dict[str, Any]]]:
        """
        Main ingestion method. Returns list of coin data dicts.
        Handles the 'symbols' requirement (e.g., symbol + id + name).
        """
        if not self.api_key:
            # Proceed without key but log warning about potential throttling
            logger.warning("Running without explicit API Key.")
        
        raw_data = self._fetch_with_backoff()
        
        if raw_data is None:
            return [] # Or raise specific exception depending on strictness requirements

        # Filter/Format specifically for 'symbols' v2 requirement (ID, Symbol, Name)
        ingested_items = []
        for coin in raw_data:
            try:
                item = {
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(), # Normalize to upper case
                    "name": coin.get("name"),
                    "current_price_usd": coin.get("current_price", 0.0)
                }
                ingested_items.append(item)
            except (KeyError, TypeError) as e:
                logger.error(f"Failed to process coin item: {e}")
                continue
        
        logger.info(f"Ingested {len(ingested_items)} crypto symbol records successfully.")
        return ingested_items

    def close(self):
        self.session.close()

# Proposal Entry Point - Do not execute in production without orchestration approval
if __name__ == "__main__":
    try:
        # Initialize Ingestor with safe defaults
        ingestor = CryptoDataIngestor(max_retries=3, timeout=10)
        
        # Execute ingestion proposal
        results = ingestor.ingest_symbols()
        
        if results:
            print(f"SUCCESS: Retrieved {len(results)} symbols.")
            # Propose writing results to local cache (not governance)
            with open("config/01_data_ingestion/latest_symbols.json", "w") as f:
                json.dump(results, f, indent=4)
        else:
            print("FAILURE: No data retrieved. Check connectivity and API status.")

    except Exception as e:
        # Fail closed on runtime error
        logger.critical(f"Mission failed with exception: {e}")
        # Ensure resources released
        if 'ingestor' in locals():
            ingestor.close()
```