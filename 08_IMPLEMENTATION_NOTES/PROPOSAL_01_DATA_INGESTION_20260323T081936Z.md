---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests

# Configure logging to avoid sensitive data leakage
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

CONSTRAINTS_CONFIG = {
    "forbidden_paths": ["/04_GOVERNANCE/"],
    "max_retries": 3,
    "timeout_seconds": 10
}

def get_config() -> Dict[str, Optional[str]]:
    """Load configuration from environment without exposing credentials."""
    config = {
        "api_url": os.getenv("CRYPTO_API_ENDPOINT", "https://api.coingecko.com/api/v3"),
        "timeout": int(os.getenv("API_TIMEOUT", 10)),
        "max_retries": int(os.getenv("API_RETRIES", 3))
    }
    # Validate forbidden paths are not referenced in config values
    for key, value in config.items():
        if isinstance(value, str) and any(f"forbidden" in p.lower() for p in value):
            raise ValueError("Configuration references forbidden path patterns.")
    return config

def is_path_safe(path: str) -> bool:
    """Ensure generated paths do not violate governance constraints."""
    for forbidden_pattern in CONSTRAINTS_CONFIG["forbidden_paths"]:
        if forbidden_pattern in path:
            return False
    return True

def fetch_symbols() -> List[Dict[str, any]]:
    """Fetch and ingest crypto symbols securely."""
    try:
        config = get_config()
        headers = {}  # No hardcoded auth
        response = requests.get(
            f"{config['api_url']}/coins/list",
            headers=headers,
            timeout=config["timeout"],
            allow_redirects=True
        )
        
        if response.status_code != 200:
            logger.error(f"API Request Failed with status: {response.status_code}")
            raise Exception(f"Ingestion failure at step 3: API Response Error")

        data = response.json()
        
        # Basic validation of returned structure
        if not isinstance(data, list):
            logger.error("Unexpected data format from API.")
            return []

        return [{
            "id": symbol.get("id"),
            "symbol": symbol.get("symbol", "").upper(),
            "name": symbol.get("name")
        } for symbol in data if symbol.get("symbol")]

    except requests.exceptions.RequestException as e:
        logger.critical(f"Network error during ingestion: {e}")
        raise SystemExit(1)  # Fail closed on network issues

def sanitize_input_data(raw_data: List[Dict]) -> List[Dict]:
    """Clean and validate data to prevent injection or malformed symbols."""
    clean_data = []
    for item in raw_data:
        try:
            # Sanitize symbol names (remove special chars, ensure uppercase)
            safe_name = "".join(c for c in str(item.get("name", "")) if c.isalnum())
            item["name"] = safe_name
            
            if item.get("symbol"):
                clean_data.append({k: str(v) for k, v in item.items()})
        except Exception as e:
            logger.warning(f"Skipping malformed entry due to sanitization: {e}")
    return clean_data

def main_ingestion_task():
    """Main execution flow for data ingestion proposal."""
    try:
        logger.info("Starting Crypto Symbols Ingestion (v2)")
        
        # Step 1: Fetch
        raw_symbols = fetch_symbols()
        if not raw_symbols:
            raise SystemExit(0)

        # Step 2: Sanitize
        clean_symbols = sanitize_input_data(raw_symbols)
        
        # Step 3: Validation against local storage (simulated path safety check)
        output_path_template = "data/crypto_output_{timestamp}.json"
        safe_output_path = f"{output_path_template.replace('}', '').replace('{', '')}_{datetime.now().strftime('%Y%m%d')}"
        
        # Check constraint
        if not is_path_safe(safe_output_path):
            logger.error("Output path violates governance constraints.")
            raise SystemExit(1)

        logger.info(f"Processed {len(clean_symbols)} symbols securely.")
        return clean_symbols

    except Exception as e:
        logger.critical(f"Ingestion failed due to: {e}")
        raise

if __name__ == "__main__":
    main_ingestion_task()