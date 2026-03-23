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
from typing import Dict, Any, Optional

class CryptoBackfillProposal:
    """Secure utility class for cryptographic backfill task proposals."""
    
    # Security Constants
    FORBIDDEN_PATH = "04_GOVERNANCE"
    REQUIRED_ENV_VAR = "CRYPTO_API_KEY"
    
    def __init__(self) -> None:
        """Initialize with security checks. Fail closed if invalid state."""
        self._check_secrets()
        
    def _check_secrets(self) -> None:
        """Enforce fail-closed behavior on missing credentials."""
        api_key = os.getenv(self.REQUIRED_ENV_VAR)
        if not api_key:
            raise PermissionError(f"Constraint breach: Missing {self.REQUIRED_ENV_VAR}. Failing closed.")

    def _validate_path(self, path: str) -> None:
        """Ensure output paths do not violate governance constraints."""
        if self.FORBIDDEN_PATH in path:
            raise ValueError(f"Constraint breach: Path contains forbidden marker '{self.FORBIDDEN_PATH}'.")

    def get_ingestion_path(self) -> Optional[str]:
        """Return a safe ingestion path or None if constrained."""
        try:
            base = os.getenv("DATA_ROOT", "/data/raw")
            # Enforce constraint check
            self._validate_path(base) 
            return f"{base}/ingestion/01_DATA_E4_005/"
        except ValueError:
            return None
            
    def propose_backfill(self, start_block: int = 1000, end_block: int = 2000) -> Dict[str, Any]:
        """Generate the proposal for fetching and backfilling data."""
        path = self.get_ingestion_path()
        
        if not path:
            raise RuntimeError("Backfill cannot proceed: Forbidden or invalid paths detected.")
            
        return {
            "status": "Proposal Generated",
            "range": f"{start_block}-{end_block}",
            "target_path": path,
            "credentials_required": self.REQUIRED_ENV_VAR
        }

def main() -> None:
    """Entry point for reviewing the backfill proposal."""
    try:
        service = CryptoBackfillProposal()
        # Execute proposal logic only
        result = service.propose_backfill(1000, 2000)
        
        if not sys.argv[1].startswith('-'):
            print(f"Proposal Result:\n{result}")
            
    except (PermissionError, ValueError, RuntimeError) as e:
        # Fail closed behavior on violation
        sys.stderr.write(f"Backfill failed closed: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error during proposal generation: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```