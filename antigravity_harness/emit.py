from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from antigravity_harness.config import DataConfig, StrategyParams
from antigravity_harness.data import load_ohlc
from antigravity_harness.strategies import get_strategy


class JSONEncoder(json.JSONEncoder):
    """Custom encoder for datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


def unique_signals(  # noqa: PLR0913
    strategy_name: str, symbol: str, timeframe: str, lookback_bars: int, end_date: str, params: Dict[str, Any]
) -> str:
    """
    Runs the strategy on the latest data window and returns a JSON signal.
    This function:
    1. Loads the last N bars of data for the symbol.
    2. Runs strategy.prepare_data() to generate indicators and signals.
    3. Extracts the FINAL bar's state.
    4. Returns a JSON string with the decision.
    """

    # 1. Setup
    strat = get_strategy(strategy_name)
    strat_params = StrategyParams(**params)

    # 2. Data Loading (Auto-calculate start based on lookback + buffer)
    # We load a sufficiently large chunk to ensure indicators have warmed up.
    # For a production bridge, we might just load everything from a certain date.
    # Here, we assume the user provides a comprehensive 'start' or we default to a safe window.
    # To simplify, we will load from a static extensive start date for now, as performance for one symbol is negligible.
    data_cfg = DataConfig(interval=timeframe)
    df = load_ohlc(symbol, start="2020-01-01", end=end_date, cfg=data_cfg)

    if df.empty:
        return json.dumps({"error": f"No data found for {symbol}"}, sort_keys=True)

    # 3. Execution
    processed = strat.prepare_data(df, strat_params)

    # 4. Extract Last Bar
    last_bar = processed.iloc[-1]

    # Determine Action
    # This logic mimics the engine's check.
    # Entry has higher priority if we assume we are flat.
    # Ideally, the bridge should know current position state, but for a stateless signal emitter:
    # We report BOTH Entry and Exit signal status.

    signal_payload = {
        "timestamp": last_bar.name,
        "symbol": symbol,
        "close_price": float(last_bar["Close"]),
        "indicators": {
            "sma_fast": float(last_bar.get("SMA_FAST", 0.0)),
            "sma_slow": float(last_bar.get("SMA_SLOW", 0.0)),
            "rsi": float(last_bar.get("RSI", 0.0)),
            "atr": float(last_bar.get("ATR", 0.0)),
        },
        "signals": {
            "entry_active": bool(last_bar.get("entry_signal", False)),
            "exit_active": bool(last_bar.get("exit_signal", False)),
        },
        "params": strat_params.model_dump(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return json.dumps(signal_payload, cls=JSONEncoder, indent=2, sort_keys=True)
