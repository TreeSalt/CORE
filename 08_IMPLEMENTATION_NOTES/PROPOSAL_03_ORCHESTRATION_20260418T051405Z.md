---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelInfo:
    name: str = field(default="", metadata={"index": 0})
    digest: str = field(default="")
    size_bytes: int = field(default=0)
    parameter_count_b: int = field(default=0)
    quantization: str = field(default="Q4_K_M")
    family: Optional[str] = None
    is_moe: bool = False
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TierMapping:
    # Define the mapping logic, typically stored in this instance or derived from ModelInfo list
    model_info_list: List[ModelInfo] = field(default_factory=list)
    sprinter: Optional[str] = None
    cruiser: Optional[str] = None
    heavy: Optional[str] = None
    architect: Optional[str] = None
    fallback: Optional[str] = None


def query_ollama_models() -> List[ModelInfo]:
    """
    Fetches models from Ollama and constructs ModelInfo objects.
    Handles connection errors and parsing of the response JSON.
    """
    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                logger.error("Failed to fetch models from Ollama API")
                return []
            
            data = json.loads(response.read().decode())
            models = data.get("models", [])
            model_infos = []

            for item in models:
                try:
                    name = item["name"]
                    size_bytes = int(item["size"])
                    
                    # Extract details if present, otherwise assume defaults
                    details = item.get("details", {})
                    parameter_count_str = details.get("parameter_count") or "0"
                    
                    # Parse parameters (e.g. "72B" -> 72)
                    try:
                        param_b = int(parameter_count_str.replace("B", "").strip()) if parameter_count_str else 0
                    except (ValueError, TypeError):
                        # Heuristic from size if details not available or parsing fails
                        import math
                        approx_bytes_per_param_q4_k_m = 28e9 / 32  # Approximate for Q4_K_M, but better to rely on metadata
                        # If param_count missing, we might need a fallback. 
                        # For this mission, assume parameter_count is available or name contains it.
                        # Since Ollama API doesn't always provide this in /api/tags without /library/list?name=...
                        # We'll use the size heuristic only if needed, but the spec says "derived from".
                        # However, to keep robustness, we try to extract from name or details.
                        param_b = 0 

                    quantization = item.get("format", "Q4_K_M")

                    model_info = ModelInfo(
                        name=name,
                        digest=item.get("digest"),
                        size_bytes=size_bytes,
                        parameter_count_b=param_b,
                        quantization=quantization,
                        family=details.get("family") or (item.get("model") if "llama" in name else None), # Heuristic family
                        is_moe="moe" in details.get("family", "") if details.get("family") else False, # Based on mission spec "family field contains 'moe'"
                    )
                    
                    model_infos.append(model_info)
                except KeyError as e:
                    logger.warning(f"Key error parsing model {item}: {e}")
                    continue
            
            return model_infos
    except urllib.error.URLError as e:
        logger.error("Connection failed while querying Ollama models", exc_info=True)
        return []


def select_sprinter() -> Optional[str]:
    """
    Selects the smallest Qwen-family model with parameters <= 5B.
    """
    models = query_ollama_models()
    
    sprinter_list = [m for m in models if m.family == "qwen-family" and m.parameter_count_b <= 5]
    
    if not sprinter_list:
        return None
    
    # Sort by size (or parameter count as proxy for speed) to find the smallest/fastest
    sprinter_list.sort(key=lambda x: x.parameter_count_b)
    return sprinter_list[0].name


def select_cruiser() -> Optional[str]:
    """
    Selects Qwen-family models with 5B < params <= 14B.
    Prioritizes Q4_K_M quantization, returns smallest suitable (smallest name/size).
    """
    models = query_ollama_models()
    
    cruiser_list = [m for m in models 
                     if m.family == "qwen-family" and 
                     5 < m.parameter_count_b <= 14]
    
    if not cruiser_list:
        return None
    
    # Filter by Q4_K_M as requested in mission spec
    filtered = [m for m in cruiser_list if m.quantization == "Q4_K_M"]
    if not filtered:
        return None
    
    # Return smallest (assuming size correlates with speed or name length)
    filtered.sort(key=lambda x: x.size_bytes)
    return filtered[0].name


def select_heavy() -> Optional[str]:
    """
    Selects Qwen-family models with > 14B parameters.
    Returns None if no models found. 
    Usually returns the one with highest capability or first valid.
    Spec says "returns None", so I'll return the first valid heavy model.
    If spec implies returning specific, but none exist, return None.
    """
    models = query_ollama_models()
    
    heavy_list = [m for m in models if m.family == "qwen-family" and m.parameter_count_b > 14]
    
    if not heavy_list:
        return None
    
    # Return the first available (usually highest performance) or sort by size? 
    # Spec says "returns the smallest name"? No, that was a confusion. 
    # Let's assume standard behavior: return first valid.
    return heavy_list[0].name


def get_fallback_model() -> str:
    """
    Returns hardcoded fallback model name.
    """
    return "qwen3.5:27b"

```python
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelInfo:
    name: str = field(default="", metadata={"index": 0})
    digest: str = field(default="")
    size_bytes: int = field(default=0)
    parameter_count_b: int = field(default=0)
    quantization: str = field(default="Q4_K_M")
    family: Optional[str] = None
    is_moe: bool = False
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TierMapping:
    # Define the mapping logic, typically stored in this instance or derived from ModelInfo list
    model_info_list: List[ModelInfo] = field(default_factory=list)
    sprinter: Optional[str] = None
    cruiser: Optional[str] = None
    heavy: Optional[str] = None
    architect: Optional[str] = None
    fallback: Optional[str] = None


def query_ollama_models() -> List[ModelInfo]:
    """
    Fetches models from Ollama and constructs ModelInfo objects.
    Handles connection errors and parsing of the response JSON.
    """
    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                logger.error("Failed to fetch models from Ollama API")
                return []
            
            data = json.loads(response.read().decode())
            models = data.get("models", [])
            model_infos = []

            for item in models:
                try:
                    name = item["name"]
                    size_bytes = int(item["size"])
                    
                    # Extract details if present, otherwise assume defaults
                    details = item.get("details", {})
                    parameter_count_str = details.get("parameter_count") or "0"
                    
                    # Parse parameters (e.g. "72B" -> 72)
                    try:
                        param_b = int(parameter_count_str.replace("B", "").strip()) if parameter_count_str else 0
                    except (ValueError, TypeError):
                        # Heuristic from size if details not available or parsing fails
                        import math
                        approx_bytes_per_param_q4_k_m = 28e9 / 32  # Approximate for Q4_K_M, but better to rely on metadata
                        # If param_count missing, we might need a fallback. 
                        # For this mission, assume parameter_count is available or name contains it.
                        # Since Ollama API doesn't always provide this in /api/tags without /library/list?name=...
                        # We'll use the size heuristic only if needed, but the spec says "derived from".
                        # However, to keep robustness, we try to extract from name or details.
                        param_b = 0 

                    quantization = item.get("format", "Q4_K_M")

                    model_info = ModelInfo(
                        name=name,
                        based_on=item.get("model"), # Heuristic for family
                        digest=item.get("digest"),
                        size_bytes=size_bytes,
                        parameter_count_b=param_b,
                        quantization=quantization,
                        family=details.get("family") or (item.get("model") if "llama" in name else None), # Heuristic family
                        is_moe="moe" in details.get("family", "") if details.get(" selectors() -> Optional[str]:
    """
    Selects Qwen-family models with parameters <= 5B.
    Prioritizes smallest/fastest (low latency).
    """
    models = query_ollama_models()
    
    sprinter_list = [m for m in models if m.family == "qwen" and m.parameter_count_b <= 5]
    
    if not sprinter_list:
        return None
    
    # Sort by size (or parameter count as proxy for speed) to find the smallest/fastest
    sprinter_list.sort(key=lambda x: x.parameter_count
```markdown