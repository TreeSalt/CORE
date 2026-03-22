from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from mantis_core.accelerators.vector_cache import VectorCache
from mantis_core.config import (
    DataConfig,
    EngineConfig,
    GateThresholds,
    StrategyParams,
)
from mantis_core.models import SimulationContext
from mantis_core.utils import infer_periods_per_year


class SimulationContextBuilder:
    """
    Fluent builder for SimulationContext.
    Centralizes physics-aware initialization (period derivation).
    """

    def __init__(self):
        self._strategy_name: Optional[str] = None
        self._strategy: Optional[Any] = None
        self._params: Optional[StrategyParams] = None
        self._data_cfg: Optional[DataConfig] = None
        self._engine_cfg: Optional[EngineConfig] = None
        self._thresholds: Optional[GateThresholds] = None
        self._symbol: Optional[str] = None
        self._start: Optional[str] = None
        self._end: Optional[str] = None
        self._gate_profile: str = "equity_fortress"
        self._override_df: Optional[pd.DataFrame] = None
        self._intelligence: Dict[str, Any] = {}
        self._debug: bool = False
        self._out_dir: Optional[Path] = None
        self._vector_cache: Optional[VectorCache] = None

    def with_debug(self, enabled: bool) -> SimulationContextBuilder:
        self._debug = enabled
        return self

    def with_vector_cache(self, cache: Optional[VectorCache]) -> SimulationContextBuilder:
        self._vector_cache = cache
        return self


    def with_out_dir(self, out_dir: Optional[Path]) -> SimulationContextBuilder:
        self._out_dir = out_dir
        return self

    def with_strategy(self, name: str, instance: Any) -> SimulationContextBuilder:
        self._strategy_name = name
        self._strategy = instance
        return self

    def with_params(self, params: StrategyParams) -> SimulationContextBuilder:
        self._params = params
        return self

    def with_data_cfg(self, cfg: DataConfig) -> SimulationContextBuilder:
        self._data_cfg = cfg
        return self

    def with_engine_cfg(self, cfg: EngineConfig) -> SimulationContextBuilder:
        self._engine_cfg = cfg
        return self

    def with_thresholds(self, thresholds: GateThresholds) -> SimulationContextBuilder:
        self._thresholds = thresholds
        return self

    def with_symbol(self, symbol: str) -> SimulationContextBuilder:
        self._symbol = symbol
        return self

    def with_window(self, start: str, end: str) -> SimulationContextBuilder:
        self._start = start
        self._end = end
        return self

    def with_gate_profile(self, profile: str) -> SimulationContextBuilder:
        self._gate_profile = profile
        return self

    def with_override_df(self, df: Optional[pd.DataFrame]) -> SimulationContextBuilder:
        self._override_df = df
        return self

    def with_intelligence(self, intel: Dict[str, Any]) -> SimulationContextBuilder:
        self._intelligence = intel
        return self

    def build(self) -> SimulationContext:
        """Harmonize physics and return IMMUTABLE context."""
        if (
            self._strategy_name is None
            or self._params is None
            or self._data_cfg is None
            or self._engine_cfg is None
            or self._thresholds is None
            or self._symbol is None
            or self._start is None
            or self._end is None
        ):
            missing = []
            if self._strategy_name is None:
                missing.append("strategy_name")
            if self._params is None:
                missing.append("params")
            if self._data_cfg is None:
                missing.append("data_cfg")
            if self._engine_cfg is None:
                missing.append("engine_cfg")
            if self._thresholds is None:
                missing.append("thresholds")
            if self._symbol is None:
                missing.append("symbol")
            if self._start is None:
                missing.append("start")
            if self._end is None:
                missing.append("end")
            raise ValueError(f"Incomplete SimulationContext: missing {missing}")

        # Physics Injection (Centralized)
        periods_year = infer_periods_per_year(self._data_cfg.interval, is_crypto=self._engine_cfg.is_crypto)

        # Harmonize EngineConfig with derived physics
        final_engine_cfg = self._engine_cfg.model_copy(update={"periods_per_year": periods_year})

        return SimulationContext(
            strategy_name=self._strategy_name,
            strategy=self._strategy,
            params=self._params,
            data_cfg=self._data_cfg,
            engine_cfg=final_engine_cfg,
            thresholds=self._thresholds,
            symbol=self._symbol,
            start=self._start,
            end=self._end,
            gate_profile=self._gate_profile,
            override_df=self._override_df,
            intelligence=self._intelligence,
            debug=self._debug,
            out_dir=self._out_dir,
            vector_cache=self._vector_cache,
        )
