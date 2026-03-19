---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

To resolve the dependency resolution errors and implement strict routing logic based on `DOMAINS.yaml`, the following function updates the tier selection process:

1.  **Logic**: It checks token length to escalate from `sprinter` -> `cruiser` -> `heavy`.
2.  **Config**: It loads `primary_tier` and specific model identifiers (e.g., `cruiser_model`) safely without using the hallucinated `config_manager`.
3.  **Reasoning**: It returns a detailed reason string explaining the tier selection based on load or token count.

```python
import yaml
import os
from pathlib import Path

def select_tier(domain, mission_text):
    # Define standard thresholds for escalation (adjustable)
    TOKEN_THRESHOLD_CROSSOVER = 4096
    TOKEN_THRESHOLD_HEAVY = 8192
    
    # Construct safe path or use environment variable if set
    # This avoids hallucinated 'config_manager'
    try:
        config_path = os.environ.get('DOMAINS_PATH', str(Path(__file__).parent / 'configs' / 'DOMAINS.yaml'))
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Determine base tier from configuration
        primary_tier = config.get(domain.lower(), {}).get('primary_tier', 'sprinter')
        model_config = config.get(domain.lower(), {})
        cruiser_model = model_config.get('cruiser_model', None)
        heavy_model = model_config.get('heavy_model', None)
        
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        # Fallback defaults if config fails or domain is unknown
        primary_tier = 'sprinter'
        cruiser_model = None
        heavy_model = None

    # Determine tier based on token count escalation
    current_token_count = len(mission_text.split()) # Simple heuristic for token proxy
    
    final_tier = primary_tier
    selected_model_id = None
    reason = f"Using default tier: {primary_tier}"
    
    if current_token_count > TOKEN_THRESHOLD_HEAVY:
        if heavy_model:
            selected_model_id = heavy_model
            final_tier = 'heavy'
            reason = f"Escalated to {final_tier} due to high token usage ({current_token_count} tokens). Model: {selected_model_id}"
        else:
            # Fallback if heavy model not configured
            final_tier = 'cruiser' 
            selected_model_id = cruiser_model or primary_tier
            
    elif current_token_count > TOKEN_THRESHOLD_CROSSOVER:
        if cruiser_model:
            selected_model_id = cruiser_model
            final_tier = 'cruiser'
            reason = f"Escalated to {final_tier} due to elevated token usage ({current_token_count} tokens). Model: {selected_model_id}"
        else:
            # If no cruiser model defined, fallback logic (avoid infinite recursion)
            final_tier = primary_tier
            selected_model_id = config.get('default_model') or primary_tier 
            reason = f"Escalation threshold hit ({current_token_count} tokens), but only {final_tier} available. Model: {selected_model_id}"

    else:
        # Standard tier logic, just map the text to the configured model for this tier
        # Note: The prompt says "sprinter", "cruiser", "heavy" are tiers. 
        # Usually a model ID is associated with the tier in config.
        selected_model_id = config.get('models', {}).get(final_tier, primary_tier) 
        
    return final_tier, selected_model_id or None, reason
```