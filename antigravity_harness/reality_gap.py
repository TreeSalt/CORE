import json
import os
from typing import List

import numpy as np
import pandas as pd

import antigravity_harness as _ah


class SchemaError(Exception):
    pass


def validate_schema(df: pd.DataFrame, required: List[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        msg = f"Missing columns in {name}: {missing}. Expected: {required}.\nFirst line: {df.columns.tolist()}"
        raise SchemaError(msg)


def run_reality_gap(fills_path: str, signals_path: str, outdir: str) -> str:  # noqa: PLR0915
    """
    Compare expected execution (signals) vs real fills.
    """
    print(f"👁️ REALITY GAP SENSOR: {os.path.basename(fills_path)} vs {os.path.basename(signals_path)}")
    os.makedirs(outdir, exist_ok=True)

    # 1. Load & Validate
    try:
        fills = pd.read_csv(fills_path)
        signals = pd.read_csv(signals_path)
    except Exception as e:
        raise SchemaError(f"Failed to read CSVs or files missing: {e}") from e

    req_fills = ["symbol", "side", "qty", "fill_price", "fill_ts"]
    req_signals = ["symbol", "side", "qty", "expected_price", "signal_ts"]

    validate_schema(fills, req_fills, os.path.basename(fills_path))
    validate_schema(signals, req_signals, os.path.basename(signals_path))

    # 2. Preprocess
    try:
        fills["fill_ts"] = pd.to_datetime(fills["fill_ts"])
        signals["signal_ts"] = pd.to_datetime(signals["signal_ts"])
    except Exception as e:
        raise SchemaError(f"Timestamp parsing failed: {e}") from e

    # 3. Matching Logic
    results = []
    unique_keys = set(fills[["symbol", "side"]].itertuples(index=False, name=None))

    matched_count = 0
    unmatched_fills = 0

    for sym, side in unique_keys:
        f_subset = fills[(fills["symbol"] == sym) & (fills["side"] == side)].sort_values("fill_ts").copy()
        s_subset = signals[(signals["symbol"] == sym) & (signals["side"] == side)].sort_values("signal_ts").copy()

        f_subset["fill_ts_key"] = f_subset["fill_ts"]
        s_subset["signal_ts_key"] = s_subset["signal_ts"]

        merged = pd.merge_asof(
            f_subset,
            s_subset,
            left_on="fill_ts",
            right_on="signal_ts",
            by=["symbol", "side"],
            direction="backward",
            tolerance=pd.Timedelta("1h"),
        )

        for _idx, row in merged.iterrows():
            if pd.isna(row["signal_ts"]):
                unmatched_fills += 1
                continue

            # Check qty
            if not np.isclose(row["qty_x"], row["qty_y"], rtol=0.01):
                unmatched_fills += 1
                continue

            matched_count += 1

            fill_p = row["fill_price"]
            exp_p = row["expected_price"]

            # Slippage Calculation: (fill - expected) * side_sign / expected * 10000
            # Side Sign: Buy -> +1 (higher price is + slippage), Sell -> -1 (lower price is + slippage)
            sign = 1 if str(side).upper() == "BUY" else -1
            slip_bps = (fill_p - exp_p) * sign / exp_p * 10000.0

            latency = (row["fill_ts"] - row["signal_ts"]).total_seconds()

            # Fee impact (Task 4: Fix model_fee matching)
            # Checking both 'model_fee' and 'model_fee_y' (if merged renamed it)
            f_fee = row.get("fee_x", 0.0)
            if pd.isna(f_fee):
                f_fee = 0.0

            s_fee = 0.0
            if "model_fee_y" in row:
                s_fee = row["model_fee_y"]
            elif "model_fee" in row:
                s_fee = row["model_fee"]

            if pd.isna(s_fee):
                s_fee = 0.0
            fee_imp = f_fee - s_fee

            results.append(
                {
                    "symbol": sym,
                    "side": side,
                    "fill_ts": row["fill_ts"].isoformat(),
                    "signal_ts": row["signal_ts"].isoformat(),
                    "slippage_bps": float(slip_bps),
                    "latency_sec": float(latency),
                    "fee_impact": float(fee_imp),
                }
            )

    # 4. Report Generation
    df_res = pd.DataFrame(results)

    stats: dict[str, float] = {
        "fills_rows": float(len(fills)),
        "signals_rows": float(len(signals)),
        "matched_rows": float(matched_count),
        "unmatched_rows": float(unmatched_fills),
    }

    if not df_res.empty:
        # Task 4: Add medians
        stats.update(
            {
                "slippage_bps_mean": float(df_res["slippage_bps"].mean()),
                "slippage_bps_median": float(df_res["slippage_bps"].median()),
                "slippage_bps_p95": float(df_res["slippage_bps"].quantile(0.95)),
                "latency_sec_mean": float(df_res["latency_sec"].mean()),
                "latency_sec_median": float(df_res["latency_sec"].median()),
                "latency_sec_p95": float(df_res["latency_sec"].quantile(0.95)),
            }
        )
    else:
        stats.update(
            {
                "slippage_bps_mean": 0.0,
                "slippage_bps_median": 0.0,
            }
        )

    # Save JSON
    rpt_path = os.path.join(outdir, "reality_gap_report.json")
    with open(rpt_path, "w") as f:
        json.dump({"stats": stats, "details": results}, f, indent=2, sort_keys=True)

    # Save MD
    md_path = os.path.join(outdir, "reality_gap_report.md")
    with open(md_path, "w") as f:
        f.write(f"# Reality Gap Report (Institutional v{_ah.__version__})\n\n")
        f.write(f"- **Matched**: {matched_count}\n")
        f.write(f"- **Unmatched**: {unmatched_fills}\n")
        f.write(f"- **Total Fills**: {len(fills)}\n")
        f.write(f"- **Total Signals**: {len(signals)}\n\n")

        f.write("## Metrics (Median Focus)\n")
        f.write(f"- **Slippage (Median)**: {stats.get('slippage_bps_median', 0):.2f} bps\n")
        f.write(f"- **Slippage (Mean)**: {stats.get('slippage_bps_mean', 0):.2f} bps\n")
        f.write(f"- **Latency (Median)**: {stats.get('latency_sec_median', 0):.4f}s\n")
        f.write(f"- **Latency (Mean)**: {stats.get('latency_sec_mean', 0):.4f}s\n")

    print("✅ REALITY CHECK COMPLETE")
    print(f"   Matched: {matched_count} | Slippage (Median): {stats.get('slippage_bps_median', 0):.2f} bps")
    print(f"   Report: {rpt_path}")

    return rpt_path
