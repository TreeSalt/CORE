---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PositionSizeResult:
    """Represents a calculated position size result."""
    position_size: float
    kelly_fraction: float
    max_position_pct: float
    account_value: float
    risk_exposure: float = field(default=0.0, compare=False, repr=False)


def kelly_fraction(edge: float, variance: float, fractional: float = 0.5) -> float:
    """
    Calculate the fractional kelly position fraction.
    
    Args:
        edge: Expected value advantage (win rate advantage)
        variance: Risk variance or standard deviation squared
        fractional: Kelly fraction to apply (0.5 for half-kelly, 1.0 for full)
    
    Returns:
        The calculated kelly fraction
        
    Raises:
        ValueError: If edge <= 0 or variance <= 0
    """
    if edge <= 0:
        return 0.0
    
    if variance <= 0:
        return 0.0
    
    kelly_ratio = edge / variance
    
    # Cap at full Kelly (1.0)
    capped_kelly = min(kelly_ratio, 1.0)
    
    return capped_kelly * fractional


def position_size_from_kelly(account_value: float, kelly_frac: float, max_position_pct: float) -> PositionSizeResult:
    """
    Calculate the optimal position size based on kelly fraction and max limits.
    
    Args:
        account_value: Total account balance available for trading
        kelly_frac: The kelly fraction (0.0 to 1.0 typically)
        max_position_pct: Maximum position as percentage of account value
    
    Returns:
        PositionSizeResult with calculated position size and metadata
    """
    # Calculate base position from kelly fraction
    calculated_size = account_value * kelly_frac
    
    # Apply max position limit
    max_allowed = account_value * (max_position_pct / 100.0)
    
    final_size = min(calculated_size, max_allowed)
    
    # Ensure non-negative
    final_size = max(final_size, 0.0)
    
    # Calculate risk exposure
    risk_exposure = final_size * kelly_frac
    
    return PositionSizeResult(
        position_size=final_size,
        kelly_fraction=kelly_frac,
        max_position_pct=max_position_pct,
        account_value=account_value,
        risk_exposure=risk_exposure
    )