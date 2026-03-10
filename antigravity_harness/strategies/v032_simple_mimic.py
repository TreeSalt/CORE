from typing import Any, Dict, Optional
import pandas as pd
from antigravity_harness.config import StrategyParams
from .base import Strategy

class v032_simple(Strategy):
    name: str = "v032_simple"

    def prepare_data(
        self, 
        df: pd.DataFrame, 
        params: StrategyParams, 
        intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[Any] = None
    ) -> pd.DataFrame:
        df["entry_signal"] = False
        df["exit_signal"] = False
        df["ATR"] = 0.0
        return df
