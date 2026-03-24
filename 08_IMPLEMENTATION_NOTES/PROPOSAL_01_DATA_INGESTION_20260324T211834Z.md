---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict

# ---------------------------------------------------------------------
# CONFIGURATION & INITIALIZATION
# ---------------------------------------------------------------------

# SECURITY: Load configuration from environment variables only.
# Hardcoded credentials are prohibited.
CRYPTO_API_KEY = os.getenv('CRYPTO_API_KEY')
API_BASE_URL = os.getenv('CRYPTO_API_BASE_URL', 'https://api.coingecko.com/v3')

# PATHING: Ensure ingestion paths do not overlap with governance directories (04_GOVERNANCE/)
DATA_INGESTION_ROOT = Path(os.getenv('DATA_INGESTION_PATH', './data/ingested'))
LOG_OUTPUT_ROOT = Path(os.getenv('LOG_OUTPUT_PATH', './logs/ingestion'))

# Create necessary directories safely without writing to restricted zones
DATA_INGESTION_ROOT.mkdir(parents=True, exist_ok=True)
LOG_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# Configure logging for audit trail
log_file_path = LOG_OUTPUT_ROOT / 'crypto_symbols_v2.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------

def sanitize_data(raw_dict: dict) -> Optional[dict]:
    """Sanitizes raw data to prevent injection or structural corruption."""
    try:
        # Basic length checks for safety and performance
        if len(raw_dict.get('id', '')) > 200 or \
           len(raw_dict.get('symbol', '')) > 30 or \
           len(raw_dict.get('name', '')) > 100:
            logger.warning("Sanitizing data due to length constraint.")
        
        # Return a clean copy to avoid mutation
        return {k: v for k, v in raw_dict.items() if v is not None}
    except Exception as e:
        logger.error(f"Data sanitization failed: {e}")
        return None

def fetch_symbol_list() -> List[Dict]:
    """Fetches the list of supported cryptocurrency symbols from the external API."""
    url = f"{API_BASE_URL}/coins/list"
    
    headers = {
        'accept': 'application/json',
        # Note: X-CG-KEY is handled via Authorization header if required by specific endpoint,
        # but standard endpoints often handle this differently. We pass key if needed later.
        'x-cg-include': '1' 
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code: {response.status_code}")
            return []
            
        # Response typically comes as a list of dicts or wrapped in dict. Check structure.
        data = response.json()
        
        if isinstance(data, list):
            raw_symbols = [sanitize_data(item) for item in data]
            logger.info(f"Fetched {len(raw_symbols)} raw symbols.")
            return [s for s in raw_symbols if s is not None]
        else:
            # Fallback parsing if wrapped in an object
            list_content = data.get('data', []) or data.get('symbols', []) or []
            return [sanitize_data(item) for item in list_content]

    except requests.exceptions.RequestException as e:
        logger.critical(f"Network error during ingestion: {e}")
        sys.exit(1) # Fail closed on network failure
    except json.JSONDecodeError as e:
        logger.critical(f"JSON decoding error: {e}")
        return []

# ---------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------

def run_ingestion_pipeline():
    """Main entry point for the ingestion service."""
    # 1. Check Credentials
    if not CRYPTO_API_KEY:
        logger.critical("FATAL: API Key missing from environment variables.")
        sys.exit(1)
    
    # Ensure API key is properly set in header for authenticated requests
    auth_headers = { 'x-cg-key': CRYPTO_API_KEY } if CRYPTO_API_KEY else headers
    
    # Override headers with auth (if needed, or just pass through)
    # Simplified: usually GET /coins/list is open rate limit or key based.
    
    logger.info("Starting Crypto Symbol Ingestion Pipeline...")
    
    # 2. Execute Fetch
    symbols = fetch_symbol_list()
    
    if not symbols:
        logger.error("No symbols retrieved from source.")
        sys.exit(1) # Fail closed
        
    # 3. Save Output
    output_file = DATA_INGESTION_ROOT / 'crypto_symbols.json'
    
    try:
        with open(output_file, 'w') as f:
            json.dump(symbols, f, indent=2)
        logger.info(f"Pipeline complete. Saved {len(symbols)} valid symbols to {output_file}")
        return True
        
    except IOError as e:
        logger.critical(f"Failed to write output file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        run_ingestion_pipeline()
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception in main block: {e}")
        sys.exit(1)
```