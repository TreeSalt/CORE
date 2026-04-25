---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class AggregatedSignal:
    direction: int
    strength: float
    confidence: float
    regime: str

def aggregate_signals(regime_state: str, trend_signal_value: float, weights: List[float]) -> AggregatedSignal:
    total_weight = sum(weights) if weights else 0.0
    
    if total_weight == 0:
        return AggregatedSignal(
            direction=0,
            strength=0.0,
            confidence=0.0,
            regime=regime_state
        )
    
    average_weight = total_weight / len(weights)
    weighted_value = trend_signal_value * average_weight
    
    strength_normalized = max(0.0, min(abs(weighted_value), 1.0))
    
    if weighted_value > 0:
        direction_val = 1
    elif weighted_value < 0:
        direction_val = -1
    else:
        direction_val = 0
        
    confidence_score = min(1.0, max(0.0, abs(total_weight) / 5.0))
    
    return AggregatedSignal(
        direction=direction_val,
        strength=strength_normalized,
        confidence=confidence_score,
        regime=regime_state
    )