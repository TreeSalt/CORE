from typing import List, Set

import pandas as pd


class CorrelationGuard:
    """
    Risk Intelligence Component.
    Monitors asset universe for hidden correlation risks.
    """

    @staticmethod
    def filter(returns: pd.DataFrame, threshold: float = 0.9, vol_window: int = 60) -> List[str]:
        """
        Identify pairs with correlation > threshold.
        Remove the asset with HIGHER volatility (Standard Deviation).

        Args:
            returns: DataFrame of asset returns (Pct Change).
            threshold: Correlation coefficient limit (0.0 to 1.0).
            vol_window: Lookback for volatility calculation (if returns is longer, we use full).
                        Actually, 'returns' passed here is usually the lookback window itself.

        Returns:
            List of 'Safe' symbols to keep.
        """
        if returns.empty or len(returns.columns) < 2:  # noqa: PLR2004
            return list(returns.columns)

        # 1. Compute Correlation Matrix
        # fillna(0) handles assets with zero variance (constant price)
        corr_matrix = returns.corr().fillna(0.0).abs()

        # 2. Compute Volatility (for tie-breaking)
        # We use the provided returns window.
        vols = returns.std()

        to_drop: Set[str] = set()
        columns = returns.columns

        # Iterate over upper triangle
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                asset_a = columns[i]
                asset_b = columns[j]

                if asset_a in to_drop or asset_b in to_drop:
                    continue

                val = corr_matrix.iloc[i, j]

                if val > threshold:
                    # Conflict!
                    # Drop the one with Higher Volatility
                    vol_a = vols[asset_a]
                    vol_b = vols[asset_b]

                    if vol_a > vol_b:
                        to_drop.add(asset_a)
                    else:
                        to_drop.add(asset_b)

        remaining = [c for c in columns if c not in to_drop]
        return remaining
