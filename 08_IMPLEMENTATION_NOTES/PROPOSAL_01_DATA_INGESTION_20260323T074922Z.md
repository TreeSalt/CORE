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
import logging
import json
import time
from datetime import datetime
import urllib.request
import urllib.parse
import ssl

# Safe log directory to avoid Governance path violations (04_GOVERNANCE/)
LOG_DIR = "/tmp/ingestion_logs" 
LOG_FILE = f"{LOG_DIR}/{datetime.now().strftime('%Y-%m-%d')}.log"

def get_logger():
    """Initialize a logger writing to safe paths only."""
    # Safety check: Ensure we are not pointing at Governance directories
    if "/04_GOVERNANCE/" in LOG_DIR:
        raise ValueError("Invalid log directory. Cannot write to Governance path.")
    
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except PermissionError:
        print(f"Warning: Cannot create logs directory at {LOG_DIR}. Failing safely.", file=sys.stderr)
        sys.exit(1) # Fail closed

    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = get_logger()

def fetch_crypto_market_data(api_endpoint: str, auth_token: str) -> dict | None:
    """
    Fetches cryptocurrency market data securely using standard library.
    Uses urllib instead of requests to ensure imports are resolvable without external dependencies.
    Implements fail-closed behavior on all exceptions.
    """
    if not api_endpoint or not api_endpoint.startswith("http"):
        logger.error("Invalid or missing API endpoint.")
        raise SystemExit("Ingestion failed due to invalid endpoint configuration.")

    if not auth_token:
        logger.critical("Authentication token is missing.")
        raise SystemExit("Ingestion aborted: Missing credentials.")

    # Prepare headers without exposing secrets in logs
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    try:
        payload = b'{}'
        
        req = urllib.request.Request(
            api_endpoint,
            data=payload, 
            headers=headers, 
            method='GET'
        )
        
        # Use SSL context for secure HTTP connections (standard library only)
        context = ssl.create_default_context()
        
        with urllib.request.urlopen(req, timeout=5, context=context) as response:
            if response.status == 200:
                json_str = response.read().decode('utf-8')
                logger.info("Successfully retrieved data from API.")
                return json.loads(json_str)
            else:
                logger.error(f"API returned status code {response.status}.")
                raise SystemExit(f"API error: {response.status}")
                
    except urllib.error.HTTPError as e:
        logger.critical(f"HTTP Error {e.code}: {e.reason}")
        raise SystemExit("Ingestion failed due to HTTP error.")
    except urllib.error.URLError as e:
        logger.critical(f"Network error: {e.reason}")
        raise SystemExit("Ingestion failed due to network connectivity issues.")
    except json.JSONDecodeError as e:
        logger.critical(f"JSON parsing error: {str(e)}")
        raise SystemExit("Ingestion failed due to JSON decoding error.")
    except Exception as e:
        logger.critical(f"Unexpected exception during ingestion: {e}")
        raise SystemExit("Unhandled exception in data ingestion pipeline.")

def main():
    """Main execution function."""
    # Load configuration from environment (No hardcoding)
    api_endpoint = os.getenv("CRYPTO_API_ENDPOINT")
    auth_token = os.getenv("CRYPTO_API_BEARER_TOKEN")

    if not api_endpoint or not auth_token:
        logger.error("Missing required API endpoint or token. Exiting.")
        sys.exit(1) # Fail closed
    
    print(f"Configuration validated for {api_endpoint}")
    
    while True:
        try:
            data = fetch_crypto_market_data(api_endpoint, auth_token)
            if data:
                # Log success or process data here
                logger.info("Ingestion cycle completed successfully.")
                pass 
        except SystemExit:
            # Re-raise SystemExit to exit immediately on errors
            raise
        except Exception as e:
            logger.error(f"Cycle failed with exception: {e}")
        
        time.sleep(60)

if __name__ == "__main__":
    main()
```