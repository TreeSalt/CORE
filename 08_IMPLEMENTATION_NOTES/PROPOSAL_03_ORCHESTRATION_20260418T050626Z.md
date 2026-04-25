---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelInfo:
    name: str
    parameter_size: str
    parameter_count_b: float
    family: str
    is_moe: bool
    quantization: str
    size_bytes: int


@dataclass(frozen=True)
class TierMapping:
    sprinter: Optional[str] = None
    cruiser: Optional[str] = None
    heavy: Optional[str] = None
    architect: Optional[str] = None
    fallback: Optional[str] = None
    loaded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def query_ollama_models() -> List[ModelInfo]:
    """Performs a GET to Ollama's /api/tags endpoint with 10-second timeout."""
    url = "http://localhost:11434/api/tags"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:
        logger.error(f"Failed to query Ollama models: {e}")
        raise RuntimeError(f"Connection failure or invalid response from Ollama: {e}")
    
    if not isinstance(data, list):
        logger.error(f"Unexpected response format from Ollama: {type(data)}")
        raise RuntimeError("Invalid JSON structure received from Ollama")
    
    models = []
    for model in data:
        try:
            name = str(model.get('name', ''))
            family = str(model.get('family', ''))
            
            # Parse parameter count
            param_str = str(model.get('size', '0'))  # Ollama uses 'size' or may use 'details.params'
            if isinstance(model, dict) and 'details' in model:
                param_str = model.get('details', {}).get('format') or param_str
            
            # Try to get parameter_size directly from the response or parse
            parameter_size = str(model.get('name', ''))
            
            # For parsing parameter count, check common fields
            size_val = model.get('size', 0)
            
            # Some Ollama responses have 'details' with 'params' field
            if isinstance(model, dict):
                detail = model.get('details', {})
                if detail:
                    params_str = str(detail.get('params', ''))
                    if 'B' in params_str:
                        param_count_b = float(params_str.replace('B', '').replace(',', '').strip())
                        parameter_size = params_str
            else:
                param_count_b = 0.0
                parameter_size = ""
            
            # Alternative: check for standard model info format
            if not parameter_size or parameter_size == "":
                param_size_str = str(model.get('parameter_size', '') or model.get('size', ''))
                if 'B' in param_size_str:
                    import re
                    match = re.search(r'([\d.]+)B', param_size_str)
                    if match:
                        parameter_size = param_size_str
                        param_count_b = float(match.group(1))
                    
            # If still empty, use size_bytes as fallback
            if not parameter_size or (parameter_size == "" and isinstance(model, dict)):
                param_count_b = 0.0
                
            models.append(ModelInfo(
                name=name,
                parameter_size=parameter_size,
                parameter_count_b=float(str(model.get('params', model.get('size', ''))).replace('B', '').strip() or "0"),
                family=family,
                is_moe='moe' in family.lower(),
                quantization=str(model.get('quantization', 'Q4_K_M')),
                size_bytes=int(model.get('size', 0) / (1024**3)) if model.get('size', 0) > 0 else 0
            ))
        except (TypeError, ValueError, KeyError) as e:
            logger.warning(f"Could not parse model {model}: {e}")
    
    return models


def select_sprinter(models: List[ModelInfo]) -> Optional[str]:
    """Returns the smallest qwen-family model with parameter_count_b <= 5.0."""
    candidates = [
        m for m in models 
        if 'qwen' in m.name.lower() and m.parameter_count_b <= 5.0
    ]
    
    if not candidates:
        return None
    
    # Prefer Q4_K_M over Q4_0
    q4_k_m = [m for m in candidates if m.quantization == 'Q4_K_M']
    q4_0 = [m for m in candidates if m.quantization == 'Q4_0']
    
    if q4_k_m:
        return min(q4_k_m, key=lambda x: x.parameter_count_b).name
    
    if q4_0:
        return min(q4_0, key=lambda x: x.parameter_count_b).name
    
    return None


def select_cruiser(models: List[ModelInfo]) -> Optional[str]:
    """Returns the smallest qwen-family model with 5.0 < parameter_count_b <= 14.0."""
    candidates = [
        m for m in models 
        if 'qwen' in m.name.lower() and 5.0 < m.parameter_count_b <= 14.0
    ]
    
    if not candidates:
        return None
    
    # Prefer Q4_K_M quantization
    q4_k_m = [m for m in candidates if m.quantization == 'Q4_K_M']
    
    if q4_k_m:
        return min(q4_k_m, key=lambda x: x.parameter_count_b).name
    
    # Return smallest regardless of quantization if no Q4_K_M available
    return min(candidates, key=lambda x: x.parameter_count_b).name


def select_heavy(models: List[ModelInfo]) -> Optional[str]:
    """Returns a model with 25.0 <= parameter_count_b <= 32.0, preferring MoE."""
    candidates = [
        m for m in models 
        if 25.0 <= m.parameter_count_b <= 32.0
    ]
    
    if not candidates:
        return None
    
    # Strongly prefer MoE architectures over dense ones
    moe_candidates = [m for m in candidates if m.is_moe]
    
    if moe_candidates:
        # Among MoE candidates of similar size, prefer code-specialized models
        coder_candidates = [m for m in moe_candidates if 'coder' in m.name.lower()]
        
        if coder_candidates:
            return min(coder_candidates, key=lambda x: x.parameter_count_b).name
        
        return min(moe_candidates, key=lambda x: x.parameter_count_b).name
    
    # Fall back to dense models if no MoE candidates exist
    return min(candidates, key=lambda x: x.parameter_count_b).name


def select_architect(models: List[ModelInfo]) -> Optional[str]:
    """Returns the largest available MoE model with parameter_count_b >= 30.0."""
    moe_candidates = [
        m for m in models 
        if m.is_moe and m.parameter_count_b >= 30.0
    ]
    
    if not moe_candidates:
        logger.debug("No MoE models >= 30B available, falling back to heavy tier selection")
        return select_heavy(models)
    
    # Prefer non-coder MoE for broader reasoning capabilities
    non_coder_moe = [m for m in moe_candidates if 'coder' not in m.name.lower()]
    
    if non_coder_moe:
        return max(non_coder_moe, key=lambda x: x.parameter_count_b).name
    
    # If all available MoE >= 30B are coder models, use the largest regardless of specialization
    return max(moe_candidates, key=lambda x: x.parameter_count_b).name


def load_tier_mapping() -> TierMapping:
    """Queries Ollama models and populates the tier mapping."""
    try:
        models = query_ollama_models()
        
        mapping = TierMapping(
            sprinter=select_sprinter(models),
            cruiser=select_cruiser(models),
            heavy=select_heavy(models),
            architect=select_architect(models)
        )
        
        # Set fallback to the largest available model in the list
        if models:
            mapping.fallback = max(models, key=lambda x: x.parameter_count_b).name
            
    except RuntimeError as e:
        logger.error(f"Failed to load tier mapping: {e}")
        return TierMapping(loaded_at=datetime.now(timezone.utc).isoformat())
    
    return mapping


def get_model_for_tier(tier: str) -> Optional[str]:
    """Returns the model name for a given tier string."""
    valid_tiers = {"sprinter", "cruiser", "heavy", "architect", "fallback"}
    
    if tier not in valid_tiers:
        raise ValueError(f"Invalid tier '{tier}'. Valid tiers: {', '.join(sorted(valid_tiers))}")
    
    mapping = load_tier_mapping()
    return getattr(mapping, tier)


def describe_mapping(mapping: TierMapping) -> str:
    """Returns a human-readable description for logging."""
    lines = []
    
    # Sprinter tier with MoE annotation if applicable
    if mapping.sprinter:
        lines.append(f"Sprinter: {mapping.sprinter}")
        
    if mapping.cruiser:
        lines.append(f"Cruiser: {mapping.cruiser}")
        
    if mapping.heavy:
        lines.append(f"Heavy: {mapping.heavy}")
        if 'moe' in str(mapping.heavy).lower():
            lines[-1] += " (MoE)"
            
    if mapping.architect:
        lines.append(f"Architect: {mapping.architect}")
        if 'moe' in str(mapping.architect).lower():
            lines[-1] += " (MoE)"
        
    # Always include fallback since it's set even when no models are available
    if mapping.fallback or not any([
        mapping.sprinter, 
        mapping.cruiser, 
        mapping.heavy, 
        mapping.architect
    ]):
        lines.append(f"Fallback: {mapping.fallback}")
    
    return "\n".join(lines)


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     # Load tier mapping and log the result
#     try:
#         mapping = load_tier_mapping()
#         logging.basicConfig(level=logging.INFO)
#         logger.info(describe_mapping(mapping))
#         
#         # Access individual tiers
#         for tier in ["sprinter", "cruiser", "heavy", "architect"]:
#             model = get_model_for_tier(tier)
#             if model:
#                 logging.info(f"{tier.capitalize()} tier: {model}")
#     except Exception as e:
#         logger.error(f"Error loading tier mapping: {e}")

```python
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelInfo:
    name: str
    parameter_size: str
    parameter_count_b: float
    family: str
    is_moe: bool
    quantization: str
    size_bytes: int


@dataclass(frozen=True)
class TierMapping:
    sprinter: Optional[str] = None
    cruiser: Optional[str] = None
    heavy: Optional[str] = None
    architect: Optional[str] = None
    fallback: Optional[str] = None
    loaded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def query_ollama_models() -> List[ModelInfo]:
    """Performs a GET to Ollama's /api/tags endpoint with 10-second timeout."""
    url = "http://localhost:11434/api/tags"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:
        logger.error(f"Failed to query Ollama models: {e}")
        raise RuntimeError(f"Connection failure or invalid response from Ollama: {e}")
    
    if not isinstance(data, list):
        logger.error(f"Unexpected response format from Ollama: {type(data)}")
        raise RuntimeError("Invalid JSON structure received from Ollama")
    
    models = []
    for model in data:
        try:
            name = str(model.get('name', ''))
            family = str(model.get('family', ''))
            
            # Parse parameter count - handle different response formats
            detail = model.get('details', {})
            params_str = ""
            if detail and 'params' in detail:
                params_str = str(detail['params'])
            
            # Also check 'size' field directly
            size_field = model.get('size', 0)
            if not params_str and size_field > 0:
                # Extract from bytes if available
                import math
                size_gb = size_field / (1024**3)
                # Estimate parameters roughly based on size, but use actual param string if present
                
            # Standard approach: check for parameter count in common formats
            if params_str:
                # Handle "7B", "7.5B", etc.
                import re
                match = re.search(r'([\d.]+)B', params_str)
                if match:
                    parameter_size = params_str
                    param_count_b = float(match.group(1))
            else:
                # Try size field
                if isinstance(size_field, (int, float)):
                    try:
                        param_count_b = float(size_field / 4e9)  # Assume Q4 by default
                        parameter_size = f"{param_count_b:.2f}B"
                    except:
                        parameter_size = ""
                        param_count_b = 0.0
                
            models.append(ModelInfo(
                name=name,
                parameter_size=parameter_size,
                parameter_count_b=float(str(model.get('params', model.get('size', ''))).replace('B', '').strip() or "0"),
                family=family,
                is_moe='moe' in family.lower(),
                quantization=str(model.get('quantization', 'Q4_K_M')),
                size_bytes=int(model.get('size', 0) / (1024**3)) if model.get('size', 0) > 0 else 0
            ))
        except (TypeError, ValueError, KeyError) as e:
            logger.warning(f"Could not parse model {model}: {e}")
    
    return models


def select_sprinter(models: List[ModelInfo]) -> Optional[str]:
    """Returns the smallest qwen-family model with parameter_count_b <= 5.0."""
    candidates = [
        m for m in models 
        if 'qwen' in m.name.lower() and m.parameter_count_b <= 5.0
    ]
    
    if not candidates:
        return None
    
    # Prefer Q4_K_M over Q4_0
    q4_k_m = [m for m in candidates if m.quantization == 'Q4_K_M']
    q4_0 = [m for m in candidates if m.quantization == 'Q4_0']
    
    if q4_k_m and q4_0:
        # Choose the one with highest parameter count to maximize context window utilization
        best_q4km = max(q4_k_m, key=lambda x: x.parameter_count_b)
        best_q40 = max(q4_0, key=lambda MoE models >= 30B should be used for architect tier.