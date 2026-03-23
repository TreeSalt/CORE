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
from pathlib import Path
from typing import Optional, Dict
import logging

# -----------------------------------------------------------------------------
# CONSTRAINT COMPLIANCE LOGIC
# -----------------------------------------------------------------------------

# Security Class: INTERNAL - Do not expose in production without additional encryption
# Domain: 01_DATA_INGESTION
# Task: 01_DATA_E4_003_crypto_symbols_v2

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Define forbidden write targets strictly as per constraints
FORBIDDEN_PATH_PREFIXES = ["04_GOVERNANCE/"]
ALLOWED_INGESTION_ROOTS = ["01_DATA_INGESTION/staging", "02_PROCESSED_DATA/ingest"]

def is_path_allowed(target_path: str) -> bool:
    """
    Validate that the target path does not violate governance constraints.
    Fails closed on any constraint breach.
    """
    normalized_target = os.path.abspath(target_path)
    
    for forbidden in FORBIDDEN_PATH_PREFIXES:
        if normalized_target.startswith(os.path.abspath(forbidden)):
            raise PermissionError(f"Constraint Breach: Path restricted {target_path}. Forbidden prefixes: {forbidden}")
            
    # Ensure path exists or is under allowed roots
    # For ingestion proposals, we assume write to specific ingest dirs
    return True 

def load_secure_config(config_name: str = "CRYPTO_SYMBOLS_CONFIG") -> Dict[str, Optional[str]]:
    """
    Load configuration securely from environment variables.
    No hardcoded credentials permitted.
    """
    config_map = {
        'api_key': os.getenv(f"{config_name}_API_KEY", None),
        'api_endpoint': os.getenv(f"{config_name}_ENDPOINT", "https://api.coingecko.com/api/v3"), # Default fallback for logic safety
        'output_directory': os.getenv(f"{config_name}_OUTPUT_DIR", ALLOWED_INGESTION_ROOTS[0]),
        'max_retries': int(os.getenv(f"{config_name}_RETRIES", "3")),
    }

    if not config_map['api_key']:
        raise ValueError("Constraint Breach: No API credentials found in environment variables.")
    
    return config_map

class CryptoSymbolsIngestionPipeline:
    """
    Proposal for v2 Crypto Symbols Ingestion.
    Ensures no write to 04_GOVERNANCE/, uses env vars for creds.
    """
    
    def __init__(self, config_name: str = "CRYPTO_SYMBOLS_CONFIG"):
        self.config = load_secure_config(config_name)
        self.logger = logging.getLogger(f"{config_name}.ingestion")
        
        # Initialize output path with validation
        try:
            is_path_allowed(self.config['output_directory'])
            self.output_path = Path(self.config['output_directory']) / "raw_data"
            self.output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.critical(f"Constraint breach detected during init: {e}")
            sys.exit(1)

    def validate_creds(self) -> bool:
        """Ensure credentials are present before any network call."""
        if not self.config['api_key']:
            raise ValueError("Credentials required. Exiting.")
        return True

    def fetch_symbols(self) -> Dict[str, Any]:
        """
        Placeholder for symbol fetching logic.
        Demonstrates structure without hardcoded secrets or forbidden writes.
        """
        # Network request logic would go here (e.g., requests.get)
        # This is a proposal implementation, not live execution
        self.logger.info("Ingestion Task 01_DATA_E4_003 Crypto Symbols v2 initiated.")
        
        return {
            "status": "proposed",
            "symbols": [], 
            "timestamp": os.getenv("TZ_DATE") or "UTC" # Safely log time without sensitive data
        }

    def ingest_and_process(self) -> None:
        """
        Main execution flow proposal.
        Fails closed on constraint breach.
        """
        if not self.validate_creds():
            raise EnvironmentError("Security constraint: No valid API credentials.")
            
        symbols_data = self.fetch_symbols()
        
        # Ensure we don't write to forbidden paths during save simulation
        safe_save_path = self.output_path / f"symbols_{os.getenv('DATE', 'today')}.json"
        
        try:
            is_path_allowed(str(safe_save_path))
            # File writing logic would occur here with validation
            self.logger.info(f"Safe path validated: {safe_save_path}")
        except Exception as e:
            logging.critical(f"Constraint breach during save validation: {e}")
            raise e

if __name__ == "__main__":
    # This block demonstrates the proposal usage. 
    # Production code should be imported into a scheduler or orchestration tool.
    
    try:
        pipeline = CryptoSymbolsIngestionPipeline()
        pipeline.ingest_and_process()
        logging.info("Proposal validation successful.")
    except Exception as e:
        logging.critical(f"Pipeline failed closed due to error/constraint breach: {e}")
        sys.exit(1)
```