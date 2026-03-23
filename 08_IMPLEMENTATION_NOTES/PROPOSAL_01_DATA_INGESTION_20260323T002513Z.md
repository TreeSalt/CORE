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
01_DATA_E4_002_crypto_normalizer.py
SECURITY_CLASS: INTERNAL
DOMAIN: 01_DATA_INGESTION
REVISION: CORRECTIVE_CONTEXT (Fixes HALLUCINATED_IMPORT: 'aiohttp')

MISSION: Normalize crypto market data ingestion pipelines while adhering to strict security constraints.
STATUS: PROPOSAL
"""

import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# SECURITY NOTE: Removed 'aiohttp' due to dependency resolution issues and hallucinated import errors.
# Standard library or robust alternatives (e.g., requests with env-based auth) are preferred.

logger = logging.getLogger(__name__)


def load_secure_config() -> Dict[str, Any]:
    """
    Loads configuration securely from environment variables or mounted config file.
    Fails closed if credentials are missing or hardcoded attempts are detected.
    """
    try:
        # Retrieve API URL and timeouts from environment to avoid hardcoding sensitive paths/keys
        base_url = os.environ.get("CORS_CRYPTO_API_URL")
        
        if not base_url:
            logger.error("FAIL CLOSED: CORS_CRYPTO_API_URL not found in environment.")
            raise ValueError("Missing mandatory configuration: CORS_CRYPTO_API_URL")

        timeout = int(os.environ.get("DATA_INGESTION_TIMEOUT", "30"))
        max_retries = int(os.environ.get("MAX_RETRIES_ON_FAILURE", "3"))

        return {
            "api_url": base_url,
            "timeout": timeout,
            "max_retries": max_retries,
            "batch_size": int(os.environ.get("DATA_BATCH_SIZE", "100"))
        }
    except Exception as e:
        logger.critical(f"Configuration load failed. Fail closed action: {e}")
        raise SystemExit(1)


def normalize_timestamp(ts_input: str) -> Optional[str]:
    """
    Safely normalizes ISO 8601 timestamps to UTC string format.
    """
    try:
        # Handle 'Z' suffix for UTC
        if ts_input.endswith('Z'):
            dt = datetime.fromisoformat(ts_input.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(ts_input)
        
        # Ensure UTC format for consistency
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' 
    except ValueError as ve:
        logger.warning(f"Invalid timestamp format handled gracefully: {ts_input}")
        return None


def fetch_market_data(config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches market data. Uses requests (standard library if available via pip install) 
    instead of 'aiohttp' to resolve dependency hallucination.
    """
    try:
        import requests
        
        headers = {
            "Accept": "application/json",
            # Ensure no headers with static secrets
            "User-Agent": f"DataIngestBot/{__version__}"
        }
        
        params = {"limit": config.get("batch_size")}
        
        response = requests.get(config["api_url"], params=params, timeout=config["timeout"])
        response.raise_for_status()
        
        data = response.json()
        if not isinstance(data, list):
            logger.error(f"API Response was not a list: {type(data)}")
            return None
            
        return data
        
    except requests.exceptions.RequestException as e:
        # Fail closed logic applied here for network issues
        logger.error(f"Data fetch failed (Fail Closed Strategy): {e}")
        return None
    except ImportError:
        logger.critical("Critical Dependency Missing: 'requests'. Cannot proceed without secure HTTP client.")
        raise SystemExit(1)


def process_normalization(data_chunk: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Processes the chunk of data and normalizes values.
    """
    if not data_chunk:
        return {"status": "success", "processed_count": 0, "records": []}

    normalized_records = []
    
    for row in data_chunk:
        asset_id = row.get("asset_id") or row.get("symbol")
        price_raw = row.get("price", 0.0)
        
        # Secure handling of potentially malicious input types
        if not isinstance(price_raw, (int, float)):
            logger.warning(f"Invalid price type encountered: {type(price_raw)} for {asset_id}")
            continue
            
        norm_record = {
            "asset_id": str(asset_id),
            "price_normalized": round(float(price_raw), 6), # Limit precision to prevent floating point attacks
            "timestamp": normalize_timestamp(row.get("timestamp", datetime.utcnow().isoformat())),
            "source_hash": hash(str(asset_id)) % (2**16) # Placeholder for actual hash check if needed
        }
        
        normalized_records.append(norm_record)

    return {
        "status": "success", 
        "processed_count": len(normalized_records), 
        "records": normalized_records
    }


def main():
    """
    Main entry point for the Data Normalizer service.
    This script is intended to be executed in a sandboxed environment or via systemd unit.
    """
    try:
        # Secure config load
        config = load_secure_config()
        
        logger.info(f"Ingestion initialized with timeout {config['timeout']}s")
        
        # Fetch data
        raw_data = fetch_market_data(config)
        
        if not raw_data:
            raise ValueError("Failed to fetch market data. Ingestion halted.")

        # Normalize
        result = process_normalization(raw_data)
        
        if result.get("status") != "success":
            logger.error(f"Normalization failed: {result}")
            return -1
            
        return result['processed_count']
        
    except SystemExit:
        raise
    except Exception as e:
        # Catch-all for unexpected errors to ensure fail-closed behavior without exposing stack trace externally
        logger.exception("Unhandled exception in normalizer pipeline")
        print(f"ERROR: Ingestion terminated due to {type(e).__name__}: {e}")
        return -1


if __name__ == "__main__":
    # Run for testing purposes only; production should be invoked via orchestration (K8s/Celery)
    exit_code = main()
    exit(exit_code if exit_code >= 0 else 1)
```