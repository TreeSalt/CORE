from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StrategyMeta:
    name: str
    tier: int  # 1 or 2. 0 for Baseline/Deprecated.
    regime: str  # trend, chop, mixed, baseline
    description: str
    core_risks: List[str]
    recommended_assets: List[str]
    is_quarantined: bool = False


STRATEGY_CATALOG: Dict[str, StrategyMeta] = {
    "v032_simple": StrategyMeta(
        name="v032_simple",
        tier=0,
        regime="baseline",
        description="Simple Moving Average Crossover (Baseline). For pipeline verification only.",
        core_risks=["No regime filter", "High drawdown", "parameter sensitivity"],
        recommended_assets=["BTC-USD", "ETH-USD"],
        is_quarantined=True,
    ),
    "v040_alpha_prime": StrategyMeta(
        name="v040_alpha_prime",
        tier=2,
        regime="mixed",
        description="Alpha Prime: Robust multi-factor strategy with safety guards.",
        core_risks=["Lower ceiling in strong mania", "Complexity"],
        recommended_assets=["BTC-USD", "ETH-USD"],
    ),
    "v050_trend_momentum": StrategyMeta(
        name="v050_trend_momentum",
        tier=1,
        regime="trend",
        description="Trend Momentum: Aggressive trend following.",
        core_risks=["Whipsaw in chop", "Drawdown"],
        recommended_assets=["BTC-USD", "SOL-USD"],
    ),
    "v060_bit_uni_core": StrategyMeta(
        name="v060_bit_uni_core",
        tier=1,
        regime="trend",
        description="Bit Uni Core: Universal core trend logic.",
        core_risks=["Whipsaw"],
        recommended_assets=["BTC-USD"],
    ),
    "v070_donchian_breakout": StrategyMeta(
        name="v070_donchian_breakout",
        tier=1,
        regime="trend",
        description="Donchian Breakout: Classic channel breakout with SMA filter.",
        core_risks=["False breakouts", "Lag"],
        recommended_assets=["BTC-USD", "ETH-USD"],
    ),
    "v080_volatility_guard_trend": StrategyMeta(
        name="v080_volatility_guard_trend",
        tier=2,
        regime="trend",
        description="Volatility Guard Trend: Trend following with ATR-based volatility exclusion.",
        core_risks=["Misses rapid breakouts", "Filter lag"],
        recommended_assets=["BTC-USD", "ETH-USD"],
    ),
}


def get_strategy_meta(name: str) -> Optional[StrategyMeta]:
    return STRATEGY_CATALOG.get(name)
