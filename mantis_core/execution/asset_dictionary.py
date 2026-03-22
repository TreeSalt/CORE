"""
antigravity_harness/execution/asset_dictionary.py
================================================
Hardcoded asset physics for TRADER_OPS.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AssetInfo:
    asset_class: str
    multiplier: float
    tick_size: float
    min_lot: int
    periods_per_year: int

ASSET_DICTIONARY = {
    "MES": AssetInfo(
        asset_class="FUTURES",
        multiplier=5.0,
        tick_size=0.25,
        min_lot=1,
        periods_per_year=252
    )
}
