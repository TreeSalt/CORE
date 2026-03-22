from __future__ import annotations

from mantis_core.strategies.base import Strategy
from mantis_core.strategies.certified.v040_alpha_prime.v040_alpha_prime import V040AlphaPrime
from mantis_core.strategies.certified.v080_volatility_guard_trend.v080_volatility_guard_trend import (
    V080VolatilityGuardTrend,
)
from mantis_core.strategies.lab.v060_bit_uni_core.v060_bit_uni_core import V060BitUniCore
from mantis_core.strategies.lab.v070_donchian_breakout.v070_donchian_breakout import V070DonchianBreakout
from mantis_core.strategies.lab.v090_essence_follower.v090_essence_follower import V090EssenceFollower
from mantis_core.strategies.lab.v100_consensual_momentum.v100_consensual_momentum import V100ConsensualMomentum
from mantis_core.strategies.quarantine.v032_simple.v032_simple import V032Simple
from mantis_core.strategies.quarantine.v050_trend_momentum.v050_trend_momentum import V050TrendMomentum
from mantis_core.strategies.registry import STRATEGY_REGISTRY, StrategyRegistry

__all__ = [
    "REGISTRY",
    "STRATEGY_REGISTRY",
    "Strategy",
    "V032Simple",
    "V040AlphaPrime",
    "V050TrendMomentum",
    "V060BitUniCore",
    "V070DonchianBreakout",
    "V080VolatilityGuardTrend",
    "V090EssenceFollower",
    "V100ConsensualMomentum",
    "get_strategy",
]

# Pillar 2: Registry Inversion of Control
# Note: In a future iteration, we could auto-discover these from folder structure + JSON.
STRATEGY_REGISTRY.register("v032_simple", V032Simple)
STRATEGY_REGISTRY.register("v040_alpha_prime", V040AlphaPrime)
STRATEGY_REGISTRY.register("v050_trend_momentum", V050TrendMomentum)
STRATEGY_REGISTRY.register("v060_bit_uni_core", V060BitUniCore)
STRATEGY_REGISTRY.register("v070_donchian_breakout", V070DonchianBreakout)
STRATEGY_REGISTRY.register("v080_volatility_guard_trend", V080VolatilityGuardTrend)
STRATEGY_REGISTRY.register("v090_essence_follower", V090EssenceFollower)
STRATEGY_REGISTRY.register("v100_consensual_momentum", V100ConsensualMomentum)

# Legacy alias (for gradual migration)
REGISTRY = {name: STRATEGY_REGISTRY.get_class(name) for name in STRATEGY_REGISTRY.available_strategies}


def get_strategy(name: str, registry: StrategyRegistry = STRATEGY_REGISTRY) -> Strategy:
    """Sovereign retrieval of strategy instance."""
    return registry.instantiate(name)
