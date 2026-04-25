---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import json
import urllib.request
from mantis_core.orchestration.tier_loader_dataclasses import ModelInfo, TierMapping

def query_ollama_models():
    """
    Queries local Ollama instance for available models.
    
    Returns:
        list[ModelInfo]: List of available model info objects (name and size in MB).
    """
    models = []
    try:
        url = "http://127.0.0.1:11434/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            # Handle standard Ollama API response (list of dicts) or empty list/dict
            if isinstance(data, list):
                for item in data:
                    name = item.get("name", "")
                    # Get size; handle potential missing 'model_size' field or different names
                    # Ollama usually returns 'model_size' as bytes (int)
                    size_str = item.get("model_size") or item.get("size")
                    if size_str:
                        try:
                            size_bytes = int(size_str)
                            size_mb = size_bytes / (1024 ** 2) # Convert to MB
                            models.append(ModelInfo(name=name, size_mb=size_mb))
                        except (ValueError, TypeError):
                            # If not a valid integer, use a default or skip
                            continue
            elif isinstance(data, dict):
                # Handle API wrapper that returns dict with 'models' key
                if "models" in data:
                    models = query_ollama_models() # recursive for safety? No, just process inner list
                    for item in data["models"]:
                         name = item.get("name", "")
                         size_str = item.get("model_size") or item.get("size")
                         if size_str:
                             try:
                                 size_bytes = int(size_str)
                                 models.append(ModelInfo(name=name, size_mb=size_bytes / (1024 ** 2)))
                             except: pass
    except Exception:
        # Ollama might not be running or unreachable.
        pass
    
    return models

def select_sprinter(vram_limit):
    """
    Selects the smallest model that fits in the given VRAM limit.
    
    Args:
        vram_limit (int): Available VRAM in bytes.
        
    Returns:
        ModelInfo | None: The selected 'sprinter' model or None if none fit.
    """
    models = query_ollama_models()
    # Apply margin (assume 90% of limit is safe)
    effective_limit = vram_limit * 0.9
    
    valid_models = [m for m in models if m.size_mb <= effective_limit]
    if not valid_models:
        return None
    
    # Select the smallest
    best_fit = min(valid_models, key=lambda x: x.size_mb)
    return best_fit

def select_cruiser(vram_limit):
    """
    Selects a mid-sized model that fits in the given VRAM limit.
    
    Args:
        vram_limit (int): Available VRAM in bytes.
        
    Returns:
        ModelInfo | None: The selected 'cruiser' model or None if none fit.
    """
    models = query_ollama_models()
    effective_limit = vram_limit * 0.9
    
    valid_models = [m for m in models if m.size_mb <= effective_limit]
    if not valid_models:
        return None
    
    # Select a 'mid-sized' model (median size of available ones)
    valid_models.sort(key=lambda x: x.size_mb)
    mid_idx = len(valid_models) // 2
    if mid_idx >= len(valid_models):
        return valid_models[-1] # fallback to largest fitting
    
    return valid_models[mid_idx]

def select_heavy(vram_limit):
    """
    Selects the largest model that fits in the given VRAM limit.
    
    Args:
        vram_limit (int): Available VRAM in bytes.
        
    Returns:
        ModelInfo | None: The selected 'heavy' model or None if none fit.
    """
    models = query_ollama_models()
    effective_limit = vram_limit * 0.9
    
    valid_models = [m for m in models if m.size_mb <= effective_limit]
    if not valid_models:
        return None
    
    # Select the largest
    best_fit = max(valid_models, key=lambda x: x.size_mb)
    return best_fit

if __name__ == "__main__":
    # Example usage to construct TierMapping if needed or run locally
    import sys
    # Assuming 8GB VRAM for example
    vram_bytes = int(8 * 1024**2)
    
    sprinter = select_sprinter(vram_bytes)
    cruiser = select_cruiser(vram_bytes)
    heavy = select_heavy(vram_bytes)
    
    if sprinter or cruiser or heavy: # Check not all None
        tier_mapping = TierMapping(sprinter=sprinter, cruiser=cruiser, heavy=heavy)
        print(f"Tier Mapping built: {tier_mapping}")
        
        # Display selected models
        print(f"Sprinter: {sprinter.name if sprinter else 'None'}")
        print(f"Cruiser: {cruiser.name if cruiser else 'None'}")
        print(f"Heavy: {heavy.name if heavy else 'None'}")
```<|endoftext|><|im_start|>user
Now, I want you to write me code