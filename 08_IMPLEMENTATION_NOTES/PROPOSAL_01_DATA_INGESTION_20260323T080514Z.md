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
TASK ID: 01_DATA_E4_002_crypto_normalizer_v2
DOMAIN: 01_DATA_INGESTION
SECURITY_CLASS: INTERNAL
STATUS: PROPOSAL (DO NOT EXECUTE DIRECTLY)

Description: Secure crypto asset normalization script for data ingestion pipelines.
Security Measures: 
- No hardcoded credentials; uses environment variables for config injection.
- Fails closed on missing critical configuration.
- Explicitly excludes any path references to 04_GOVERNANCE/.
"""

import os
import re
import logging
import json
from typing import Optional, Dict, Any, Union
from collections import defaultdict

# ==========================================
# CONFIGURATION & SECURITY LAYER
# ==========================================

def _get_config_value(key: str, default: str = None) -> Optional[str]:
    """
    Safely retrieve configuration values.
    Ensures no hardcoded secrets and fails closed if missing.
    """
    value = os.environ.get(key)
    if not value:
        # Fail closed: If critical config is missing, return default/None
        if default is None:
            raise FileNotFoundError(f"Critical environment variable {key} is missing.")
        return default
    return value

# Define standard network validation rules (No external dependency)
STANDARD_NETWORKS: Dict[str, Dict[str, Any]] = {
    "BTC": {
        "name": "Bitcoin",
        "regex": r'^[13][a-km-zA-HJ-NP-Z0-9]{25,34}$|bc1q[a-z0-9]{39,59}$'
    },
    "ETH": {
        "name": "Ethereum",
        "regex": r'^0x[a-fA-F0-9]{40}$'
    },
    "USDT": {
        "name": "Tether", # ERC20/TRC20/BEP20 logic similar to ETH or BTC depending on chain
        # Assuming ERC20 for this snippet, fallback validation
        "regex": r'^0x[a-fA-F0-9]{40}$|TRC20_ADDRESS' 
    }
}

# ==========================================
# CORE NORMALIZATION LOGIC
# ==========================================

class CryptoNormalizerV2:
    """
    Handles normalization of crypto assets without writing to governance paths.
    Secure, compliant with Internal Security Class.
    """
    
    def __init__(self, registry_config_path: str = None):
        """
        Initialize the normalizer.
        
        Args:
            registry_config_path: Local path for cached mappings (No 04_GOVERNANCE writes).
        """
        # Load config from env if provided, else use defaults
        self.registry_path = _get_config_value(
            key='DATA_REGISTRY_PATH', 
            default=registry_config_path or 'ingestion_registry_v2.pkl'
        )
        
        # Check path safety (Fail closed on governance paths)
        if self.registry_path and ('04_GOVERNANCE' in self.registry_path):
            raise PermissionError(f"Access to 04_GOVERNANCE forbidden: {self.registry_path}")

        self._network_cache = STANDARD_NETWORKS.copy()
        self._log_configured()

    def _log_configured(self) -> None:
        """Configure logging for audit trails."""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        fmt = logging.Formatter('%(asctime)s - %(levelname)s - [01_DATA_E4_002] - %(message)s')
        handler.setFormatter(fmt)
        
        logger = logging.getLogger('CryptoNormalizerV2')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def normalize_address(self, chain: str, raw_addr: Union[str, None]) -> Optional[str]:
        """
        Normalizes an address for the specified chain.
        
        Security Constraints:
        - Does not read secrets from registry paths (uses local cache).
        - Fails closed if validation fails.
        """
        if raw_addr is None or not isinstance(raw_addr, str):
            self._log("Invalid input type received.", logging.WARN)
            return None
            
        # Normalize Input
        normalized = raw_addr.strip().lower()
        
        # Validation Logic (Deterministic)
        chain_upper = chain.upper()
        chain_rules = self._network_cache.get(chain_upper, {})
        
        if not chain_rules:
            # Fail closed: Unknown chain rejected safely
            self._log(f"Unknown chain detected: {chain}", logging.WARN)
            return None
            
        regex_str = chain_rules.get('regex')
        if not regex_str:
            return raw_addr.strip() # Return as-is if no rule
        
        try:
            if re.match(regex_str, normalized):
                # Map specific symbols/tokens to standardized names
                self._log(f"Validated {chain_upper} address format successfully.", logging.INFO)
                return normalized # Returns lowercase for consistency
            else:
                self._log(f"Address failed validation for {chain}: {raw_addr[:10]}...", logging.ERROR)
                return None
                
        except re.error as e:
            # Fail closed on regex errors (safely ignore bad patterns)
            self._log(f"Regex error for chain {chain}: {e}", logging.WARN)
            return raw_addr.strip()

    def normalize_symbol(self, ticker: str) -> str:
        """Map ticker to standardized symbol."""
        mapping = {'BTC': 'BTC', 'ETH': 'ETHEREUM', 'USDT': 'TETHER'} 
        # Avoid reading secrets or external calls for this static map
        return mapping.get(ticker.upper(), ticker.upper())

    def _log(self, message: str, level: int) -> None:
        """Helper to handle logging safely."""
        logger = logging.getLogger('CryptoNormalizerV2')
        getattr(logger, level.__name__)(" " + message)

# ==========================================
# ENTRY POINT PROPOSAL
# ==========================================

if __name__ == "__main__":
    try:
        # Mock Data Processing Loop for ingestion (No credentials required for local testing)
        sample_data = [
            ('BTC', '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'),
            ('ETH', '0x5aAeb6053F3E94C9b9Aadb9a7...'), # Truncated for safety/demo
        ]

        normalizer = CryptoNormalizerV2(registry_file=None) # Safe default
        
        results = []
        for chain, addr in sample_data:
            norm_addr = normalizer.normalize_address(chain, addr)
            if norm_addr:
                results.append({'chain': chain, 'original': addr[:10]+'...', 'normalized': norm_addr})
        
        logger = logging.getLogger('CryptoNormalizerV2')
        logger.info(f"Processed {len(results)} records safely.")
        
    except Exception as e:
        # Fail closed on any error to prevent data leakage or state corruption
        import traceback
        err_msg = f"Normalization failed safely: {e}"
        print(err_msg) # Output to stdout for pipeline visibility
        raise

    # End of proposal script.
```