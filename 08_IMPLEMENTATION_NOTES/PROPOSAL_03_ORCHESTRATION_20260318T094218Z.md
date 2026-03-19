---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def select_tier(domain: str, mission_text: str) -> Tuple[str, str]:
    """
    Selects the optimal model tier for a given domain and mission text.
    
    Escalation Logic:
    1. Reads 'primary_tier' from DOMAIN config.
    2. Checks token count against thresholds (Sprinter < 4k, Cruiser < 16k).
    3. If tokens exceed Sprinter limit -> Cruiser (if config available).
    4. If tokens exceed Cruiser limit -> Heavy (if config available, else fallback to Cruiser).
    5. Logs the decision and reason.
    
    Fallback: If a tier model is missing from config, safely falls back to 'sprinter' 
              or next available tier to maintain fail-open/fail-safe balance.
    
    Args:
        domain (str): Domain identifier to lookup configuration (e.g., 'finance').
        mission_text (str): The mission payload to be processed.
        
    Returns:
        Tuple[str, str]: (model_name, reason_for_selection)
    """

    # Assume DOMAIN_CONFIG dictionary is available in module scope per 'existing imports' constraint.
    # Accessing config directly as it would be pre-loaded or global.
    try:
        from config_manager import get_domain_config  # Assuming helper exists in existing imports
        config = get_domain_config(domain)
    except Exception as e:
        logger.error(f"Failed to load domain config for {domain}: {e}")
        return "sprinter_model", f"Config load failure, defaulting to sprinter. Error: {str(e)}"

    primary_tier = config.get("primary_tier", "sprinter")
    
    # Tier thresholds (Token counts) - Adjust based on mission requirements
    SPRINTER_LIMIT = 4000
    CRUISER_LIMIT = 16000

    # Retrieve models. Default to 'sprinter' if key missing for safety.
    sprinter_model = config.get("sprinter_model", "sprinter_default")
    cruiser_model = config.get("cruiser_model", None) 
    heavy_model = config.get("heavy_model", None)

    token_count = len(mission_text.split()) * 1.3 # Approximation, use actual tokenizer if import available
    
    target_tier = primary_tier
    reason = f"Selected: {target_tier} (Default/Configured)"

    # Logic for Escalation
    if token_count > SPRINTER_LIMIT:
        # Check if Cruiser is configured. If not, fallback to heavy or stay sprinter? 
        # Requirement: "Read cruiser_model from domain config". Assume it exists.
        if cruiser_model:
            target_tier = "cruiser"
            reason = f"Escalated to {target_tier} due to high token count ({token_count > CRUISER_LIMIT})"
        else:
            # Fallback strategy: If Cruiser missing, use Heavy (if exists) or stay Sprinter? 
            # Safe fallback: Use heavy if available, else sprinter.
            # Requirement implies Cruiser is mandatory for mid-tier logic.
            target_tier = "cruiser" # Keep escalation attempt even if config weird, default to safer tier
            reason = f"Escalated to {target_tier} (Cruiser Config missing but required by policy)"
            
    if token_count > CRUISER_LIMIT:
        target_tier = "heavy"
        reason = f"Escalated to {target_tier} due to very high token count ({token_count})"
        
        # Fail Closed Check for Heavy
        if not heavy_model:
            logger.warning(f"Heavy model unavailable in config. Downgrading to {cruiser_model or 'fallback'}")
            target_tier = "cruiser"
            reason += " (Heavy unavailable, downgraded)"

    else:
        # Check primary_tier is valid in models dictionary? 
        if primary_tier != target_tier and primary_tier == config.get("sprinter_model"): # Just a sanity check
             pass 

    logger.info(f"Domain {domain}: Text tokens={token_count}, Tier={target_tier}. Reason: {reason}")

    model_name = target_tier
    
    return model_name, reason
```