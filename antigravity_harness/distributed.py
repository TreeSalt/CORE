try:
    import ray  # type: ignore
except ImportError:
    ray = None
from typing import Any, Dict, Optional, Type

import pandas as pd

from antigravity_harness.config import DataConfig, EngineConfig, GateThresholds, StrategyParams
from antigravity_harness.context import SimulationContextBuilder
from antigravity_harness.models import MetricSet, SimulationResult
from antigravity_harness.runner import SovereignRunner
from antigravity_harness.strategies.base import Strategy


def init_ray(num_cpus: Optional[int] = None) -> None:
    """
    Initialize Ray if not already running.
    """
    if ray is None:
        raise ImportError("Ray is not installed.")
    if not ray.is_initialized():
        ray.init(num_cpus=num_cpus, ignore_reinit_error=True)


if ray:

    @ray.remote
    class BacktestWorker:
        """
        Ray Actor that holds data in memory and executes backtests.
        """

        def __init__(
            self, data_map: Dict[Any, pd.DataFrame], strategy_cls: Type[Strategy], engine_config: EngineConfig
        ):
            # Pin data in memory
            self.data_map = data_map
            self.strategy_cls = strategy_cls
            self.engine_config = engine_config

            # Instantiate strategy once? No, strategy might be stateful per run?
            # Actually Strategy class is stateless or re-instantiated.
            # _run_one calls get_strategy().
            # Here we pass class.
            # We instantiate per run to be safe.
            self.strategy_instance = strategy_cls()

        def calibrate_one(  # noqa: PLR0913
            self,
            symbol: str,
            params: StrategyParams,
            data_cfg: DataConfig,
            thresholds: GateThresholds,
            start: str,
            end: str,
            gate_profile: str = "equity_fortress",
            interval: str = "1d",
        ) -> SimulationResult:
            """
            Distributed version of calibration._run_one.
            Uses in-memory data via 'override_df'.
            """
            # Lookup data: Try specific (Sym, Interval) first, then Sym
            key = (symbol, interval)
            df = self.data_map.get(key, self.data_map.get(symbol))

            if df is None:
                return SimulationResult(
                    params=params.model_dump(),
                    status="FAIL",
                    profit_status="FAIL",
                    safety_status="FAIL",
                    fail_reason=f"Data not found for {symbol} {interval}",
                    warns=[],
                    gate_results=[],
                    metrics=MetricSet(),
                )

            # Instantiate strategy
            strat = self.strategy_cls()
            runner = SovereignRunner()

            ctx = (
                SimulationContextBuilder()
                .with_strategy(strat.name, strat)
                .with_params(params)
                .with_data_cfg(data_cfg.model_copy(update={"interval": interval}))
                .with_engine_cfg(self.engine_config)
                .with_thresholds(thresholds)
                .with_symbol(symbol)
                .with_window(start, end)
                .with_gate_profile(gate_profile)
                .with_override_df(df)
                .build()
            )

            return runner.run_simulation(ctx)

else:
    # Dummy class for Import safety
    class BacktestWorker:  # type: ignore[no-redef]
        pass
