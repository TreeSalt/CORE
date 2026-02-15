import os
import sys

import pandas as pd

# Adjust path to find the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import re

from antigravity_harness import __version__ as pkg_version
from antigravity_harness.gates import _calc_annual_vol
from antigravity_harness.utils import infer_periods_per_year, safe_read_csv, safe_to_csv


def test_version_truth():
    print(f"Testing Version Truth... Current: {pkg_version}")
    # Verify semantic versioning format (X.Y.Z)
    assert re.match(r"^\d+\.\d+\.\d+$", pkg_version), f"Invalid version format: {pkg_version}"
    # Verify we are at least at the Dragonproof baseline (4.4.0)
    major, minor, _ = map(int, pkg_version.split("."))
    assert major >= 4 and minor >= 4, f"Version too low for Dragonproof: {pkg_version}"


def test_schema_stability():
    print("Testing Schema Stability...")
    tmp_path = "test_empty.csv"
    df = pd.DataFrame()
    safe_to_csv(df, tmp_path, index=False)

    if not os.path.exists(tmp_path):
        raise AssertionError("safe_to_csv failed to create file")

    df_read = safe_read_csv(tmp_path)
    if not df_read.empty:
        raise AssertionError("safe_read_csv failed to return empty dataframe")

    os.remove(tmp_path)
    print("  [x] Empty CSV handling passed")


def test_physics_hardening():
    print("Testing Physics Hardening...")
    # 1. Infer Periods
    assert infer_periods_per_year("1d") == 365, "1d inference failed"  # noqa: PLR2004
    assert infer_periods_per_year("1h") == 8760, "1h inference failed"  # noqa: PLR2004
    assert infer_periods_per_year("4H") == 2190, "4h inference failed"  # noqa: PLR2004
    print("  [x] Interval inference passed")

    # 2. Volatility Calculation (Intraday Fix)
    dates = pd.date_range("2023-01-01", periods=100, freq="1h")
    prices = [100.0]
    for i in range(1, 100):
        prices.append(prices[-1] * (1.0 + (0.01 if i % 2 == 0 else -0.01)))

    df = pd.DataFrame({"Close": prices}, index=dates)

    # Calculate for 1h (8760 periods/year)
    # Vol should be approx std * sqrt(8760). std of returns is ~0.01.
    # 0.01 * 93.6 = 0.936
    vol = _calc_annual_vol(df, periods=8760)
    expected_approx = 0.936

    print(f"  Vol (1h, 1% moves): {vol:.4f} (Expected ~{expected_approx:.4f})")

    # Tolerance
    assert abs(vol - expected_approx) < 0.1, f"Vol mismatch: {vol} vs {expected_approx}"  # noqa: PLR2004
    print("  [x] Volatility calculation passed")


if __name__ == "__main__":
    try:
        test_version_truth()
        test_schema_stability()
        test_physics_hardening()
        print("\n✅ All Compliance Tests Passed.")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
