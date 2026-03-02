import sys
print("Starting")
import pandas as pd
print("Imported pandas")
from antigravity_harness.regimes import RegimeConfig, _infer_single_regime
print("Imported antigravity_harness")
cfg = RegimeConfig(trend_th_entry=0.6, trend_th_exit=0.3)
print("Config created")
label, _, _, is_trending, _ = _infer_single_regime(
    dz=0.45, vr=1.0, dd=0.0, disp=1.0, td=1.0, rv=0.15,
    avg_corr=0.0, corr_z=0.0, was_trending=False, was_high_vol=False, cfg=cfg
)
print(f"Result 1: {label}")
label, _, _, is_trending, _ = _infer_single_regime(
    dz=0.45, vr=1.0, dd=0.0, disp=1.0, td=1.0, rv=0.15,
    avg_corr=0.0, corr_z=0.0, was_trending=True, was_high_vol=False, cfg=cfg
)
print(f"Result 2: {label}")
print("Finished")
