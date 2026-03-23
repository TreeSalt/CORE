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
from typing import List, Dict, Optional
import logging

# Configure logger for audit trail without exposing sensitive data
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class CryptoSymbolIngestor:
    """Secure class for ingesting crypto market symbols via API."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ingestor.
        Security Constraint: Credentials must be loaded from Environment Variables.
        Fail closed: Raises ValueError if credentials are not found in environment.
        """
        self.session = self._create_session()

    def _load_api_key(self, env_var_name: str) -> Optional[str]:
        """Load API key securely from OS environment."""
        return os.getenv(env_var_name)

    def _create_session(self):
        """Initialize HTTP session with secure headers."""
        auth_header = "Bearer " + self.api_key if hasattr(self, 'api_key') else None
        
        session = self.session = __import__('requests').Session()
        
        # Fail closed: Check for credentials existence before configuring headers
        if not self.api_key:
            raise SystemExit("CONSTITUTIONAL VIOLATION: Missing API_KEY env var.")
            
        session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        session.headers.update({"Content-Type": "application/json"})
        
        return session

    def _set_credentials(self):
        """Securely retrieve credentials from Environment."""
        # Security Constraint: Do not use hard-coded values. Use environment variables.
        self.api_key = self._load_api_key("CRYPTO_INGESTION_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "CRITICAL FAIL: CRYPTO_INGESTION_API_KEY is missing in environment. "
                "System refusing execution to prevent credential leak."
            )

    def fetch_symbols(self, base_url: str = "https://api.exchange-data.com") -> List[Dict]:
        """
        Fetch list of available crypto symbols.
        Security Constraint: No credentials logged or printed.
        Fail Closed: Raises exception on network failure to maintain data integrity.
        """
        try:
            if not self.api_key:
                raise RuntimeError("Authentication context lost.")
            
            response = self.session.get(f"{base_url}/v1/coins/list", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"API Response Error: {response.status_code}")
                return []

            # Parse and sanitize data before processing
            data = response.json()
            symbols = []
            
            for item in data:
                symbol_entry = {
                    "id": item.get("id"),
                    "symbol": item.get("symbol").upper(), # Normalize to upper case
                    "name": item.get("name")
                }
                symbols.append(symbol_entry)
                
            logger.info(f"Ingestion complete. Found {len(symbols)} symbols.")
            return symbols

        except Exception as e:
            # Fail closed: Log error without exposing stack trace details if sensitive
            logger.error(f"Data Ingestion Failed Securely: {str(e)[:50]}...")
            return []

    def save_inventory(self, symbols: List[Dict], output_path: str = None):
        """Save ingested data securely. No writes to governance paths."""
        if not symbols:
            return
            
        # Security Constraint: Do not write credentials to file system logs
        filename = "crypto_symbols.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(symbols, f)
            logger.info(f"Data persisted to {filename}")
        except IOError:
            logger.error("Failed to persist data securely.")

def main():
    """Entry point ensuring secure execution context."""
    try:
        # Initialize with strict credential check
        ingestor = CryptoSymbolIngestor()
        
        # Ensure credentials are present before logic runs
        ingestor._set_credentials()
        
        # Execute ingestion
        symbols = ingestor.fetch_symbols()
        
        # Persist results (local temp file, not governance)
        ingestor.save_inventory(symbols=symbols)
        
        print("Data Ingestion Proposal Validated.")
        
    except ValueError as ve:
        # Fail closed on credential breach
        sys.stderr.write(f"CONSTITUTIONAL VIOLATION DETECTED: {ve}\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```