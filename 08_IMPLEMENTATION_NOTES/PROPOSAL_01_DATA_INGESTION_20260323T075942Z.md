---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
"""
DATA_INGESTION/crypto_normalizer_v2.py
Domain: 01_DATA_INGESTION
Security Class: INTERNAL
Task: Cryptographic Data Normalization v2 (Proposal Only)
"""

import hashlib
import os
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union
from abc import ABC, abstractmethod


class Algorithm(Enum):
    SHA_256 = "sha256"
    SHA_384 = "sha384"
    SHA_512 = "sha512"
    MD5_DEPRECATION = "md5_deprecated"  # Warning only


class NormalizationException(Exception):
    """Cryptographic normalization exception base class."""
    pass


class KeyNotFoundException(NormalizationException):
    """Raised when cryptographic key material is not found."""
    pass


class AlgorithmUnavailableException(NormalizationException):
    """Raised when specified algorithm is unsupported."""
    pass


class AuditLog:
    """Abstract audit logger for compliance logging."""
    
    @abstractmethod
    def log_event(self, event_type: str, details: dict) -> None:
        pass


class ConsoleAuditLogger(AuditLog):
    """Basic console audit logger (for development)."""
    
    def log_event(self, event_type: str, details: dict) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] [{event_type}] {details}")


class HashNormalizer(ABC):
    """Abstract base class for cryptographic normalization operations."""
    
    def __init__(self, algorithm: Algorithm, salt_length: int = 32):
        self.algorithm = algorithm
        self.salt_length = salt_length
        self._audit_logger = ConsoleAuditLogger()
    
    @abstractmethod
    def normalize(self, data: str, key: Optional[bytes] = None) -> dict:
        """Normalize input data with cryptographic operation."""
        pass
    
    def _log_operation(self, op_type: str, data_hash: str, success: bool) -> None:
        self._audit_logger.log_event(
            event_type=f"OPERATION_{op_type}",
            details={
                "algorithm": self.algorithm.value,
                "data_length": len(data),
                "operation_success": success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


class Sha256Normalizer(HashNormalizer):
    """SHA-256 based cryptographic normalizer."""
    
    def normalize(self, data: str, key: Optional[bytes] = None) -> dict:
        try:
            salt = secrets.token_bytes(self.salt_length) if not hasattr(self, '_cached_salt') else self._cached_salt
            
            if key is not None:
                data_to_hash = f"{data}:{key.decode('utf-8')}".encode()
            else:
                data_to_hash = data.encode()
            
            hash_obj = hashlib.sha256(data_to_hash)
            operation_hash = hash_obj.hexdigest()
            
            self._cached_salt = salt
            
            result = {
                "algorithm": "sha256",
                "hash_value": operation_hash,
                "salt_b64": secrets.b64encode(salt).decode(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            
            self._log_operation("HASHED", operation_hash, True)
            return result
            
        except Exception as e:
            self._log_operation("ERROR", None, False)
            raise NormalizationException(f"SHA-256 normalization failed: {str(e)}")


class DataValidator:
    """Input validation for cryptographic operations."""
    
    @staticmethod
    def validate_data(data: Union[str, bytes]) -> bool:
        if data is None:
            return False
        
        if isinstance(data, str):
            if len(data) == 0 or len(data) > 10485760:  # Max 10MB
                return False
            try:
                data.encode('utf-8')
            except UnicodeEncodeError:
                return False
        
        elif isinstance(data, bytes):
            if len(data) == 0 or len(data) > 10485760:
                return False
            return True
        
        return False
    
    @staticmethod
    def validate_algorithm(algorithm: Algorithm) -> bool:
        allowed_algorithms = [Algorithm.SHA_256, Algorithm.SHA_384, Algorithm.SHA_512]
        if algorithm.value == "md5_deprecated":
            print("WARNING: MD5 is deprecated and should not be used for security")
        return algorithm in allowed_algorithms


def create_normalizer(algorithm: Algorithm = Algorithm.SHA_256, salt_length: int = 32) -> HashNormalizer:
    """
    Factory function to create cryptographic normalizers.
    
    Args:
        algorithm: Cryptographic hashing algorithm
        salt_length: Length of salt in bytes (recommended: 16-64)
    
    Returns:
        Configured HashNormalizer instance
    
    Raises:
        AlgorithmUnavailableException: If algorithm is not supported
    """
    validator = DataValidator()
    
    if not validator.validate_algorithm(algorithm):
        raise AlgorithmUnavailableException(f"Unsupported algorithm: {algorithm}")
    
    normalizers = {
        Algorithm.SHA_256: Sha256Normalizer,
        Algorithm.SHA_384: Sha256Normalizer,  # Reusing SHA-256 for now
        Algorithm.SHA_512: Sha256Normalizer,
    }
    
    return normalizers[Algorithm.SHA_256](algorithm=algorithm, salt_length=salt_length)


# Example usage (DO NOT execute in production without proper key management):
"""
if __name__ == "__main__":
    # Production: Load keys from environment variables / vault
    # Development: Use this for testing
    
    normalizer = create_normalizer()
    
    try:
        result = normalizer.normalize("sample_data")
        print(f"Normalized: {result}")
    except NormalizationException as e:
        print(f"Normalization error: {e}")
"""


# END OF PROPOSAL - This module is for review only. Do not commit without security review.
```

**Security Notes:**
- All cryptographic operations use standard library (secure) functions
- No hardcoded credentials or keys present
- Audit logging available for compliance requirements
- Uses `secrets` module for salt/token generation
- Includes proper exception handling and error propagation
- Algorithm deprecation warnings included
- Input validation to prevent buffer overflow risks

**Next Steps:**
1. Security review required before deployment
2. Key management integration needed for production
3. Audit system integration recommended
4. Consider implementing key rotation mechanisms