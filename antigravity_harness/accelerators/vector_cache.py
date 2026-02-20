from typing import Dict, Optional
import pandas as pd

class VectorCache:
    """
    O(1) Vectorized Grid Caching for the Calibration engine.
    Holds pre-computed indicator arrays to eliminate redundant pandas/numpy math 
    during hypercube parameter sweeps.
    """
    def __init__(self):
        # Format: { "SMA": { 50: pd.Series, 200: pd.Series }, "RSI": { ... } }
        self._cache: Dict[str, Dict[int, pd.Series]] = {}
    
    def put(self, indicator: str, period: int, data: pd.Series) -> None:
        if indicator not in self._cache:
            self._cache[indicator] = {}
        self._cache[indicator][period] = data
        
    def get(self, indicator: str, period: int) -> Optional[pd.Series]:
        return self._cache.get(indicator, {}).get(period)
    
    def clear(self):
        self._cache.clear()
