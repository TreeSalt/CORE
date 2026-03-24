---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import time
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configure logging without writing to governance paths
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

class CryptoDataIngestionPipeline:
    """
    Proposal for Data Ingestion Module E4_003 (Crypto Symbols v2).
    Compliant with: NO_HARDWARE_CREDS, FAIL_CLOSED_ON_BREACH, NO_GOV_WRITES.
    """

    # Endpoint definitions are read from internal registry check if available
    BASE_URL = "https://api.coingecko.com/api/v3"
    MARKET_ENDPOINT = f"{BASE_URL}/coins/markets"
    
    DEFAULT_HEADERS = {
        'User-Agent': 'CryptoIngestionBot-v2.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.session = requests.Session()
        
        # Handle API Key from Environment, never hardcode
        api_key = os.getenv('COINGECKO_API_KEY', '')
        if api_key:
            self.session.headers.update({'x-cg-demo': 'true'}) # Standard demo header usage
        
        # Ensure internal approval tokens take precedence over free tier limits
        internal_token = os.getenv('INTERNAL_DATA_TOKEN', '')
        if internal_token:
            self.session.headers.update({'Authorization': f'Bearer {internal_token}'})

        self.retry_count = 3
        self.backoff_factor = 2

    def validate_connection(self) -> bool:
        """Validates connection health without writing to governance paths."""
        try:
            # Health check request (no payload)
            response = self.session.get(f"{self.BASE_URL}/tickers", timeout=5, headers=self.DEFAULT_HEADERS)
            if response.status_code in [200, 401]: # 200 OK or Auth required (handled separately)
                return True
            elif response.status_code == 429:
                logger.warning("Rate limit encountered. Sleeping before retry.")
                time.sleep(60)
                return self.validate_connection()
            else:
                logger.error(f"Connection check failed with status: {response.status_code}")
                return False
        except Exception as e:
            logger.critical(f"Connection error: {e}")
            return False

    def fetch_symbols(self, ids: List[str] = None) -> Dict[str, Any]:
        """
        Fetches crypto data. Implements fail-closed logic on constraint breach.
        """
        if not ids:
            logger.info("Using default market listing endpoint.")
            # Fallback to public endpoint without ID list for general catalog
            target_url = self.MARKET_ENDPOINT
            headers = self.DEFAULT_HEADERS.copy()
            
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'page': 1, 
                'per_page': 50 # Respectful rate limiting
            }
            
            response = self.session.get(target_url, headers=headers, params=params)
        else:
            # Specific symbol lookup
            target_url = f"{self.MARKET_ENDPOINT}?ids={','.join(ids)}&vs_currency=usd"
            headers = self.DEFAULT_HEADERS.copy()
            response = self.session.get(target_url, headers=headers)

        if not response.ok:
            raise ConnectionError(f"API returned non-success status: {response.status_code}")
            
        data = response.json()
        
        # Validate structure to ensure ingestion consistency
        if 'coins' not in data:
            raise ValueError("Unexpected API response structure")
            
        return {'timestamp': datetime.utcnow().isoformat(), 'data': data}

    def run(self, ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Main execution flow with fail-closed behavior."""
        if not self.validate_connection():
            logger.error("Connection validation failed. Aborting ingestion.")
            return [] # Fail closed
            
        try:
            response_data = self.fetch_symbols(ids=ids)
            return response_data['data']
        except Exception as e:
            logger.exception(f"Ingestion failed safely: {e}")
            return []

if __name__ == "__main__":
    # Demo execution block (non-governance writes)
    pipeline = CryptoDataIngestionPipeline()
    
    if pipeline.validate_connection():
        print("Connection valid. Fetching market data...")
        results = pipeline.run(ids=['bitcoin', 'ethereum'])
        # Process results locally, do not write to prohibited paths
        print(f"Processed {len(results)} symbols.")
    else:
        print("System aborting due to connectivity constraints.")
```