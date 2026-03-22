"""mantis_core.catalog - Stable public API for the Strategy Catalog."""

from mantis_core.strategies.catalog import STRATEGY_CATALOG, StrategyMeta, get_strategy_meta

__all__ = ["StrategyMeta", "STRATEGY_CATALOG", "get_strategy_meta"]
