---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import hashlib
from pathlib import Path

def compute_sovereign_hash():
    """
    Dynamically computes the sovereign public key hash.
    Replaces any hardcoded or cached values to ensure live verification.
    """
    # Path configuration as per domain requirements
    pub_key_path = Path("keys/sovereign.pub")
    
    # Fail closed: Ensure path resolution works before hashing
    try:
        # Mandatory computation format: hashlib.sha256(open(path, "rb").read()).hexdigest()
        computed_hash = hashlib.sha256(open(pub_key_path, "rb").read()).hexdigest()
        
        # Log the computed hash for operator verification
        print(f"[BUILD_SYS] Computed Sovereign Pubkey Hash: {computed_hash}")
        
        return computed_hash
        
    except FileNotFoundError:
        raise RuntimeError("CRITICAL: Sovereign public key file missing. Build cannot continue.")

# Replace any existing hardcoded pin with the dynamic computation result
# Example: previously SOVEREIGN_KEY_HASH = "012345..." (HARDCODED REMOVED)
try:
    CURRENT_PINNED_HASH = compute_sovereign_hash()
except RuntimeError as build_error:
    # Fail closed on constraint breach or missing assets
    raise SystemExit(f"BUILD FAILURE: {build_error}")
```