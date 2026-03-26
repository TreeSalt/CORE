---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

To implement the `get_effective_tier` function and supporting components, we define a `TierPreference` Enum to handle different logic paths (Force vs Prefer) and a helper function for logging decisions. The core logic iterates through priority tiers based on the preference enum, checks resource constraints against `model_sizes`, and either returns the best fitting tier or `"ESCALATE"` if specific forced requirements fail.

Here is the clean implementation:

```python
from enum import Enum

class TierPreference(Enum):
    PREFER_HEAVY = 'prefer_heavy'
    PREFER_CRUISER = 'prefer_cruiser'
    PREFER_SPRINTER = 'prefer_sprinter'
    FORCE_HEAVY = 'force_heavy'
    FORCE_CRUISER = 'force_cruiser'

# Example model_sizes dict structure (can be populated dynamically)
# Format: {tier_name: (vram_cap, ram_cap, model_id, mode)}
# model_sizes = {
#     "HEAVY": (16000, 1024, "model_heavy", "fp8"), 
#     "CRUISER": (8000, 512, "model_cruiser", "fp8"),
#     "SPRINTER": (3000, 256, "model_sprinter", "quantized")
# }

def log_tier_decision(domain: str, desired: str, actual: str, reason: str) -> None:
    """Log a tier selection decision for debugging or audit."""
    print(f"[LOG] Domain={domain}, Desired={desired}, Actual={actual}, Reason={reason}")

def get_effective_tier(
    preference: TierPreference, 
    available_vram: int, 
    available_ram: int, 
    model_sizes: dict
) -> str:
    """
    Determines the effective tier based on user preference and resource availability.
    
    Args:
        preference (TierPreference): User's preferred tier logic.
        available_vram (int): Available VRAM in MB.
        available_ram (int): Available System RAM in GB (or consistent unit).
        model_sizes (dict): Dictionary mapping tier names to (vram_cap, ram_cap, model_id, mode).
    
    Returns:
        str: The name of the fitted tier (e.g., "HEAVY") or "ESCALATE" if constraints fail.
    """
    # Define list of tiers to attempt based on preference
    try_to_fit = []
    
    if preference == TierPreference.FORCE_HEAVY:
        try_to_fit = ["HEAVY"]
    elif preference == TierPreference.FORCE_CRUISER:
        try_to_fit = ["CRUISER"]
    elif preference == TierPreference.PREFER_HEAVY:
        try_to_fit = ["HEAVY", "CRUISER", "SPRINTER"]
    elif preference == TierPreference.PREFER_CRUISER:
        try_to_fit = ["CRUISER", "SPRINTER"]
    elif preference == TierPreference.PREFER_SPRINTER:
        try_to_fit = ["SPRINTER"]
    else:
        # Fallback to PREFER_HEAVY logic if invalid or default behavior desired
        try_to_fit = ["HEAVY", "CRUISER", "SPRINTER"]
    
    fitted_tier = None
    
    for tier_name in try_to_fit:
        if tier_name not in model_sizes:
            continue
        
        # Extract resource requirements and metadata (adjust indices based on your dict structure)
        # Assuming format: (vram_required, ram_required, model_id, mode)
        vram_req, ram_req, model_id, mode = model_sizes[tier_name]
        
        if available_vram >= vram_req and available_ram >= ram_req:
            fitted_tier = tier_name
            break
    
    # Check if forced scenarios failed completely
    if preference in [TierPreference.FORCE_HEAVY, TierPreference.FORCE_CRUISER] and fitted_tier is None:
        log_tier_decision("ModelScheduler", preference.value, "ESCALATE", "Forced tier unavailable")
        return "ESCALATE"

    # Check if general fallback failed
    if fitted_tier is None:
        # Only escalate if no valid tier found in preferred list AND forced lists are empty/defaulted
        # Assuming default preference allows fallback to SPRINTER. 
        # If all options exhausted, escalate.
        log_tier_decision("ModelScheduler", preference.value, "ESCALATE", "Resource mismatch across all tiers")
        return "ESCALATE"

    log_tier_decision("ModelScheduler", preference.value, fitted_tier, "Resource Fit")
    
    return fitted_tier

# Example Usage:
# preference = TierPreference.FORCE_HEAVY
# result = get_effective_tier(preference, available_vram=24000, available_ram=32, model_sizes=...)
```

### Key Features of the Implementation:
- **`TierPreference` Enum**: Ensures type safety and clear differentiation between `FORCE_...` (fails immediately) and `PREFER_...` (falls back gracefully).
- **Resource Checking**: Iterates through the `try_to_fit` list, validating available VRAM/RAM against the requirements stored in `model_sizes`.
- **Logging**: `log_tier_decision` helps debug why a specific tier was selected or why escalation occurred.
- **Fallback Logic**: If a user prefers heavy models but resources aren't enough, it gracefully falls back to lower tiers unless explicitly forced.

### Example Dict Structure for `model_sizes`:
Make sure `model_sizes` matches the unpacking logic `(vram_cap, ram_cap, model_id, mode)`:

```python
model_sizes = {
    "HEAVY": (16000, 32, "llama-70b", "fp8"),
    "CRUISER": (8000, 16, "mistral-7b", "int8"),
    "SPRINTER": (3000, 4, "tiny-lora", "quantized")
}
```

This design ensures that users can explicitly force specific hardware profiles or let the system negotiate based on available resources. If forced requirements cannot be met, the system returns `"ESCALATE"`.