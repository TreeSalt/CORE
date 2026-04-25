from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ModelInfo:
    name: str
    size_mb: int
    context_window: int
    supports_thinking: bool


@dataclass(frozen=True)
class TierMapping:
    sprinter: ModelInfo
    cruiser: ModelInfo
    heavy: ModelInfo
