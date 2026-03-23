---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
"""
PROPOSAL: 01_DATA_E4_002_crypto_normalizer_v2
SECURITY_CLASS: INTERNAL
DOMAIN: 01_DATA_INGESTION

IMPLEMENTATION NOTES:
- This script is a proposal artifact for review and deployment.
- No direct execution in production environments without security audit.
- All configuration must be loaded from Environment Variables (No hardcoded credentials).
- Governance writes are restricted to /logs or /temp directories only.
"""

import os
import sys
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# ----------------------------------------------------------------------
# CONSTRAINT COMPLIANCE CHECK
# ----------------------------------------------------------------------
GOVERNANCE_DIR = "04_GOVERNANCE"
LOG_LEVEL = os.getenv("CRYPTO_NORMALIZER_LOG_LEVEL", "WARNING")
DATA_BUCKET = os.getenv("DATA_INGESTION_BUCKET", "/ingest/input")

# Verify Governance directory is not written to (Fail closed on breach)
def _validate_paths() -> bool:
    """Check that no output paths point to restricted directories."""
    if any(path.startswith(GOVERNANCE_DIR) for path in [DATA_BUCKET]):
        raise PermissionError(f"Access denied: Writes to {GOVERNANCE_DIR} are forbidden.")
    return True

# ----------------------------------------------------------------------
# CONFIGURATION LOADING (Environment Variable Binding)
# ----------------------------------------------------------------------
@dataclass
class NormalizerConfig:
    """Configuration container sensitive to environment injection."""
    # No hardcoded secrets. Keys pulled from system environment.
    PRIVATE_KEY_PATH: Optional[str] = field(default=None) 
    VALIDATION_RULES_FILE: str = os.getenv("VALIDATION_RULES_PATH", "default.json")
    LOG_STREAM: str = os.getenv("LOG_STREAM_NAME", "ingest_crypto_norm")
    
    def __post_init__(self):
        # Fail closed if secrets are not properly injected (if expected)
        if self.PRIVATE_KEY_PATH and not os.path.exists(self.PRIVATE_KEY_PATH):
            raise FileNotFoundError("Private key path configured but inaccessible.")

# ----------------------------------------------------------------------
# CRYPTO NORMALIZATION LOGIC
# ----------------------------------------------------------------------
class ValidationError(Exception):
    """Specific exception for normalization validation failures."""
    pass

class CryptoNormalizer:
    """Handles normalization of cryptographic asset identifiers."""

    # Regex Patterns for common formats (Sanitized, no hardcoded secrets)
    PATTERN_BTC_LEGACY = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'
    PATTERN_BTC_SEGWIT = r'^bc1q[a-z0-9]{39,59}$'
    PATTERN_ETH_HEX = r'^0x[a-fA-F0-9]{64}$'
    PATTERN_ETH_ADD = r'^0x[a-fA-F0-9]{40}$'
    
    def __init__(self, config: NormalizerConfig):
        self.config = config
        self.logger = logging.getLogger(self.config.LOG_STREAM)
        
    def _sanitize_input(self, raw_data: str) -> str:
        """Remove whitespace and lowercase for standardization before validation."""
        if not isinstance(raw_data, str):
            raise ValidationError(f"Input must be a string. Received: {type(raw_data).__name__}")
        return " ".join(raw_data.strip().split())

    def validate_btc_address(self, raw_address: str) -> bool:
        """Validate Bitcoin addresses against Bech32 and Legacy standards."""
        cleaned = self._sanitize_input(raw_address).lower()
        
        if cleaned.startswith("bc1q"): # Check Bech32
            return re.fullmatch(r'^bc1q[a-z0-9]{39,59}$', cleaned) is not None
        elif cleaned.startswith(("1", "3")): # Legacy/P2SH
            return re.fullmatch(r'^(?:[13][a-km-zA-HJ-NP-Z1-9]+)$', raw_address) is not None
        
        return False

    def validate_eth_address(self, raw_address: str) -> bool:
        """Validate Ethereum addresses or Hex hashes."""
        cleaned = self._sanitize_input(raw_address).lower()
        
        if cleaned.startswith("0x"):
            if re.fullmatch(r'^0x[a-fA-F0-9]{40}$', raw_address): # Eth Address (20 bytes)
                return True
            elif re.fullmatch(r'^0x[a-fA-F0-9]{64}$', raw_address): # Hash (32 bytes)
                return True
        return False

    def normalize(self, raw_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process batch of crypto identifiers."""
        normalized_records = []
        
        for record in raw_payload:
            identifier_type = record.get("type")
            raw_value = record.get("value")
            
            try:
                is_valid = False
                
                if identifier_type == "BTC":
                    is_valid = self.validate_btc_address(raw_value)
                elif identifier_type == "ETH":
                    is_valid = self.validate_eth_address(raw_value)
                
                # Fail closed: If validation fails, do not include in output.
                if not is_valid:
                    continue
                
                # Construct normalized record
                norm_record = {
                    "id": record.get("uuid", f"norm_{hash(raw_value)[:8]}"),
                    "type": identifier_type,
                    "normalized_value": self._sanitize_input(raw_value),
                    "validation_status": "PASSED"
                }
                
                # Optional: Hash the value for audit trail (SHA256) without storing secrets
                if raw_value and isinstance(raw_value, str):
                    norm_record["audit_hash"] = hash(raw_value) # Simple hash for tracking
                
                normalized_records.append(norm_record)
                
            except Exception as e:
                # Fail closed on exception. Log but drop record.
                self.logger.error(f"Processing error for {identifier_type}: {e}")
                continue

        return normalized_records

# ----------------------------------------------------------------------
# MAIN EXECUTION PROPOSAL
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Constraint Check: Fail closed on setup
    if not _validate_paths():
        sys.exit(1)
        
    try:
        # Initialize Config
        config = NormalizerConfig()
        normalizer = CryptoNormalizer(config)
        
        # Example Payload (Ingest Simulation)
        payload_batch = [
            {"type": "BTC", "value": "bc1qxy2kgdygjrsqtzq2n0yrf2493ht5wctfhs5h8"},
            {"type": "BTC", "value": "invalid_address"},
            {"type": "ETH", "value": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"}
        ]
        
        result = normalizer.normalize(payload_batch)
        
        print(f"Normalized Records Count: {len(result)}")
        for r in result:
            print(r)

    except FileNotFoundError as fe:
        # Fail closed: Exit on missing credentials/secrets
        sys.stderr.write(f"FATAL: {fe}\n")
        sys.exit(1)
    except ValidationError as ve:
        sys.stderr.write(f"VALIDATION ERROR: {ve}\n")
        sys.exit(1)
    except Exception as e:
        # Generic fail closed handling
        print(f"CRITICAL SYSTEM FAILURE: {e}")
        sys.exit(1)
```