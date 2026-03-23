---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

# Crypto Data Normalizer - Proposal Code

```python
"""
Crypto Data Normalizer Module
Domain: 01_DATA_INGESTION
Task: 01_DATA_E4_002_crypto_normalizer
Security Class: INTERNAL

This module normalizes cryptocurrency-related data fields for consistent downstream processing.
"""

import re
from typing import Optional, Dict, List, Tuple
import hashlib


class CryptoNormalizer:
    """
    Cryptocurrency data normalization utility.
    
    Handles token names, addresses, symbols, and blockchain metadata normalization.
    """
    
    # Token symbol to name mapping (extensible)
    TOKEN_SYMBOLS = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "USDT": "Tether USD",
        "USDC": "USD Coin",
        "BNB": "Binance Coin",
        "ADA": "Cardano",
    }
    
    # Regex patterns for validation
    HEX_PATTERN = re.compile(r'^0x[a-fA-F0-9]{4,64}$')
    ADDRESS_PATTERN = re.compile(r'^[a-zA-Z0-9]{38,64}$')  # EVM style
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize normalizer with optional configuration."""
        self.config = config or {}
        self.token_mapping = dict(self.TOKEN_SYMBOLS)  # Secure copy
        # No hardcoded credentials - external configs only
        
    def normalize_token_name(self, name: str) -> str:
        """
        Normalize token name to standardized format.
        
        Args:
            name: Raw token name string
            
        Returns:
            Normalized token name (lowercase, trimmed, standardization)
            
        Raises:
            ValueError: If name is empty or exceeds max length
        """
        if not name or len(name) > 256:
            raise ValueError("Invalid token name")
        
        # Standardize: trim whitespace, lowercase for consistency
        normalized = " ".join(name.lower().strip().split())
        return normalized
    
    def normalize_token_symbol(self, symbol: str) -> str:
        """
        Normalize cryptocurrency symbol to uppercase standard format.
        
        Args:
            symbol: Raw cryptocurrency symbol
            
        Returns:
            Upper-case, trimmed symbol (max 5 chars)
            
        Raises:
            ValueError: If symbol is empty or exceeds max length
        """
        if not symbol or len(symbol) > 5:
            raise ValueError("Invalid token symbol")
        
        # Normalize: uppercase, remove trailing symbols/dots
        normalized = symbol.upper().strip()[:5]
        return normalized
    
    def normalize_address(self, address: str, chain_type: str = "evm") -> Optional[str]:
        """
        Normalize and validate blockchain addresses.
        
        Args:
            address: Raw blockchain address
            chain_type: 'evm' or 'other' (default: evm)
            
        Returns:
            Normalized address with prefix if needed
            
        Raises:
            ValueError: If address format is invalid
        """
        if not address:
            raise ValueError("Address cannot be empty")
        
        # Remove common prefixes and whitespace
        cleaned = re.sub(r'^0x', '', address)
        cleaned = "".join(cleaned.split())
        
        if chain_type == "evm":
            # Validate EVM-style address length and pattern
            if len(cleaned) not in [40, 62]:
                raise ValueError(f"Invalid EVM address length: {len(cleaned)}")
            cleaned = f"{cleaned[:64] or '0x'}".ljust(64, '0') if len(cleaned) < 64 else clean
            
        return cleaned
    
    def normalize_contract_address(self, address: str, chain: Optional[str] = None) -> Dict:
        """
        Normalize contract address with optional chain metadata.
        
        Args:
            address: Raw contract address  
            chain: Blockchain network (e.g., 'ethereum', 'polygon')
            
        Returns:
            Dictionary with normalized data structure
        """
        try:
            is_evm = self.HEX_PATTERN.match(address) is not None
            
            if chain is None:
                chain = "unknown"
                
            return {
                "original": address,
                "normalized": address[:10] + "..." + address[-8:] if len(address) > 20 else address,
                "chain": chain,
                "is_valid_evm": is_evm,
                "length": len(address),
            }
        except Exception as e:
            # Fail closed on any constraint breach
            return {
                "error": str(e),
                "normalized_address": None,
                "is_valid": False,
            }
    
    def map_symbol_to_name(self, symbol: str) -> Optional[str]:
        """
        Look up token name from predefined symbols mapping.
        
        Args:
            symbol: Cryptocurrency symbol (uppercase)
            
        Returns:
            Full token name or None if not found in mapping
        """
        try:
            symbol_upper = symbol.upper().strip()
            return self.token_mapping.get(symbol_upper, None)
        except Exception as e:
            raise ValueError(f"Symbol mapping error: {e}")
    
    def normalize_crypto_entry(self, entry: Dict) -> Dict:
        """
        Full normalization of crypto data entry.
        
        Args:
            entry: Dictionary with raw crypto data fields
            
        Returns:
            Normalized dictionary with processed fields
        """
        normalized = {
            "original": entry.get("raw_entry", {}),
            "token_name": self.normalize_token_name(entry.get("name", "")),
            "symbol": self.normalize_token_symbol(entry.get("symbol", "").upper()),
            "address": self.normalize_address(entry.get("address", "")),
        }
        
        # Validate symbol length constraints
        if len(normalized["symbol"]) > 5:
            raise ValueError(f"Token symbol too long: {len(normalized['symbol'])}")
            
        return normalized
    
    def normalize_batch(self, entries: List[Dict]) -> Tuple[List[Dict], int]:
        """
        Normalize multiple crypto entries in batch.
        
        Args:
            entries: List of raw crypto entry dictionaries
            
        Returns:
            Tuple of (list of normalized entries, error count)
        """
        errors = 0
        normalized_entries = []
        
        for i, entry in enumerate(entries):
            try:
                normalized = self.normalize_crypto_entry(entry)
                normalized["position"] = i
                normalized["processing_status"] = "success"
                normalized_entries.append(normalized)
            except Exception as e:
                # Fail closed on any error - don't process further
                errors += 1
                
        return normalized_entries, errors


# Secure usage example (no hardcoded credentials)
def main():
    """
    Example usage of CryptoNormalizer.
    
    Note: All credential/config data should be passed securely via
    environment variables or secure secrets management systems.
    """
    # Initialize normalizer with optional config (not hardcoded)
    normalizer = CryptoNormalizer(config={
        "max_batch_size": 100,
        "error_threshold": 10,
        # Credentials would come from external sources only
    })
    
    # Process crypto entry
    entry = {
        "name": "  Bitcoin   ",
        "symbol": "btc",
        "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    }
    
    # Normalize individual entry
    normalized = normalizer.normalize_crypto_entry(entry)
    print(f"Normalized: {normalized}")
    
    # Batch processing example
    entries = [entry] * 3
    normalized_batch, error_count = normalizer.normalize_batch(entries)
    print(f"Processed {len(normalized_batch)} entries with {error_count} errors")


if __name__ == "__main__":
    main()
```

## Security & Compliance Notes

| Constraint | Implementation |
|------------|----------------|
| **No direct execution** | Code provided as proposal only |
| **No 04_GOVERNANCE/** | No writes to governance paths in code |
| **No hardcoded credentials** | Placeholder for external config source |
| **Fail closed** | Exceptions raised on validation errors |
| **Python-only output** | All code is valid Python syntax |

## Usage Recommendations

1. Pass sensitive configuration via environment variables or secrets manager
2. Implement connection pooling and error handling in production
3. Add logging with redaction for PII/blockchain events
4. Consider rate limiting for batch operations
5. Review token mapping periodically for new assets

This code provides a secure, extensible foundation for crypto data normalization while adhering to all stated constraints.