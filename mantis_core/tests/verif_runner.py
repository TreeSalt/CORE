import numpy as np
import pandas as pd

from mantis_core.config import DataConfig, EngineConfig, GateThresholds, StrategyParams
from mantis_core.context import SimulationContextBuilder
from mantis_core.runner import SovereignRunner
from mantis_core.strategies import STRATEGY_REGISTRY


def test_sovereign_runner():
    print("Testing SovereignRunner...")

    # 1. Create Dummy Data
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    df = pd.DataFrame(
        {
            "Open": np.linspace(100, 110, 100),
            "High": np.linspace(101, 111, 100),
            "Low": np.linspace(99, 109, 100),
            "Close": np.linspace(100.5, 110.5, 100),
            "Volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )

    # 2. Configure
    params = StrategyParams()
    data_cfg = DataConfig(interval="1d")
    engine_cfg = EngineConfig(initial_cash=10000.0)
    thresholds = GateThresholds()

    # 3. Instantiate Runner
    runner = SovereignRunner()

    # 4. Run Simulation
    try:
        strat = STRATEGY_REGISTRY.instantiate("v032_simple")
        ctx = (
            SimulationContextBuilder()
            .with_strategy("v032_simple", strat)
            .with_params(params)
            .with_data_cfg(data_cfg)
            .with_engine_cfg(engine_cfg)
            .with_thresholds(thresholds)
            .with_symbol("TEST_SYM")
            .with_window("2023-01-01", "2023-04-10")
            .with_gate_profile("equity_fortress")
            .with_override_df(df)
            .build()
        )
        result = runner.run_simulation(ctx)
    except Exception as e:
        print(f"FAIL: Simulation crashed: {e}")
        return

    # 5. Verify Metrics (Using SimulationResult object attributes)
    try:
        gp = result.metrics.gross_profit
        gl = result.metrics.gross_loss
        tc = result.metrics.trade_count

        # Verify types
        if not isinstance(gp, (float, int)):
            print(f"FAIL: gross_profit is not float/int: {type(gp)}")
            return
        if not isinstance(gl, (float, int)):
            print(f"FAIL: gross_loss is not float/int: {type(gl)}")
            return

        print("PASS: SovereignRunner returned valid SimulationResult object.")
        print(f"Metrics: GP={gp}, GL={gl}, Trades={tc}")
    except AttributeError as e:
        print(f"FAIL: Missing expected metrics on result: {e}")
        return


if __name__ == "__main__":
    test_sovereign_runner()
