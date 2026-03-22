from typing import Dict, List

import pandas as pd


class Optimizer:
    """
    Vanguard Protocol: Mathematical Optimization Engine.
    """

    @staticmethod
    def equal_weight(symbols: List[str]) -> Dict[str, float]:
        if not symbols:
            return {}
        w = 1.0 / len(symbols)
        return {s: w for s in symbols}

    @staticmethod
    def inverse_volatility(returns: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        Weights proportional to 1/StdDev.
        returns: DataFrame of asset returns.
        """
        # Calculate recent vol
        recent = returns.iloc[-window:]
        vols = recent.std()

        # Handle zero vol (e.g. constant price)
        # Verify valid inputs
        valid_vols = vols[vols > 1e-8]  # noqa: PLR2004

        if valid_vols.empty:
            return Optimizer.equal_weight(list(returns.columns))

        inv_vols = 1.0 / valid_vols
        total_inv = inv_vols.sum()

        weights = (inv_vols / total_inv).to_dict()

        # Ensure 0 for dropped assets
        full_weights = {col: weights.get(col, 0.0) for col in returns.columns}
        return full_weights
