from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd

from antigravity_harness.config import StrategyParams
from antigravity_harness.accelerators.vector_cache import VectorCache


class Strategy(ABC):
    """Strategy interface.

    Contract:
    - prepare_data(df, params) returns df with:
        * entry_signal: bool (raw signal on bar close)
        * exit_signal: bool  (raw signal on bar close)
        * ATR: float (volatility metric for stops/sizing), REQUIRED.
    """

    name: str = "base"

    @abstractmethod
    def prepare_data(
        self, 
        df: pd.DataFrame, 
        params: StrategyParams, 
        intelligence: Optional[Dict[str, Any]] = None,
        vector_cache: Optional[VectorCache] = None
    ) -> pd.DataFrame:
        raise NotImplementedError

    def describe(self) -> Dict[str, Any]:
        return {"name": self.name}
