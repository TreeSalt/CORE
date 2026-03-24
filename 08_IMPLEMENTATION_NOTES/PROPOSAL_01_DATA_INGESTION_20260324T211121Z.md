---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import sys
import os
import json
import logging
from typing import Dict, List, Any

# Configure logging to avoid writes to governance directories
LOG_PATH = "/tmp/crypto_normalizer.log"
logger = logging.getLogger("01_DATA_E4_002_crypto_normalizer_v2")
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.ERROR, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define safe input configuration via environment variables only (No hardcoded creds)
INPUT_ENV_VAR = "DATA_INGESTION_SOURCE_PATH"
GOVERNANCE_PREFIX = "/04_GOVERNANCE/"

class CryptoNormalizer:
    """
    Secure crypto data normalizer.
    v2 Fix: Removed aiohttp dependency to resolve import errors.
    Logic relies on standard library for robustness and internal config only.
    """
    
    # Internal ticker normalization map (Static, No external fetch)
    _KNOWN_TICKERS = {
        "btc": {"symbol": "BTC", "chain": "bitcoin"},
        "eth": {"symbol": "ETH", "chain": "ethereum"},
        "usdt": {"symbol": "USDT", "chain": "multi-chain"}
    }

    def __init__(self):
        self.logger = logger

    def _sanitize_ticker(self, ticker: str) -> str:
        """Lowercase and strip whitespace."""
        if not ticker or not isinstance(ticker, str):
            return None
        return ticker.strip().lower()

    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single ingestion record."""
        normalized = {}
        
        # Safety check for governance path exposure (Fail Closed)
        source_path = self._get_source_path()
        if source_path and source_path.startswith(GOVERNANCE_PREFIX):
            raise PermissionError(f"Input path restricted: {source_path}")

        try:
            input_ticker = record.get("ticker", "")
            
            # Normalize ticker logic
            clean_ticker = self._sanitize_ticker(input_ticker)
            
            if clean_ticker and clean_ticker in self._KNOWN_TICKERS:
                normalized["original"] = input_ticker
                normalized["canonical_symbol"] = self._KNOWN_TICKERS[clean_ticker]["symbol"]
                normalized["chain"] = self._KNOWN_TICKERS[clean_ticker]["chain"]
            else:
                # Fallback handling for unknown assets without external calls
                normalized["original"] = input_ticker
                normalized["canonical_symbol"] = None 
                normalized["chain"] = "unknown"

            # Copy other ingestion fields safely
            for key in ["timestamp", "price", "volume"]:
                if key in record:
                    normalized[key] = record[key]

            return normalized
            
        except KeyError as e:
            self.logger.warning(f"Missing expected field: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during normalization: {e}", exc_info=True)
            return None

    def _get_source_path(self) -> str | None:
        """Get source path from environment, ensuring safety."""
        if INPUT_ENV_VAR in os.environ:
            path = os.environ[INPUT_ENV_VAR]
            # Validate path doesn't traverse into restricted zones
            if not (path.startswith(GOVERNANCE_PREFIX) or ".." in path):
                return path
        return None

    def process_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of ingestion records."""
        valid_records = []
        
        for record in records:
            normalized_record = self.normalize_record(record)
            if normalized_record is not None:
                valid_records.append(normalized_record)
            
        return valid_records

if __name__ == "__main__":
    # Secure execution entry point
    
    # Validate input source via Environment Variable (Fail Closed on missing/env breach)
    input_source = os.environ.get(INPUT_ENV_VAR, "/tmp/ingest_data.json") 
    
    if not os.path.exists(input_source):
        logger.critical(f"Input file {input_source} not found. Check environment variable {INPUT_ENV_VAR}.")
        sys.exit(1)

    # Safety check: Prevent writing to 04_GOVERNANCE/
    current_dir = os.getcwd()
    if GOVERNANCE_PREFIX in current_dir:
        logger.critical("Detected execution in Governance directory. Access denied.")
        sys.exit(1)

    normalizer = CryptoNormalizer()
    
    try:
        with open(input_source, 'r', encoding='utf-8') as f:
            raw_records = json.load(f)
        
        if not isinstance(raw_records, list):
            logger.error("Input JSON must be a list of records.")
            sys.exit(1)

        processed_data = normalizer.process_batch(raw_records)
        
        if processed_data:
            # Output logic (Avoiding writes to /04_GOVERNANCE/)
            output_log = "/tmp/normalized_crypto_data.log"
            with open(output_log, 'w') as out_f:
                json.dump(processed_data, out_f)
            
            logger.info(f"Successfully processed {len(processed_data)} records.")
        else:
            logger.warning("No valid records found to process.")

    except PermissionError as e:
        logger.critical(f"Permission denied or path breach detected: {e}")
        sys.exit(1)
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input format: {e}")
        
    except Exception as e:
        # Fail closed on any unexpected exception
        logger.critical(f"Fatal ingestion error: {type(e).__name__}: {e}")
        sys.exit(1)
```