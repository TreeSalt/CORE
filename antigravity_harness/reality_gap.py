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

        if merged.empty:
            continue

        # Vectorized Filters
        # Remove unmatched signals
        merged = merged.dropna(subset=["signal_ts"])
        
        # Check qty match (approx)
        # using numpy isclose vectorized
        qty_match = np.isclose(merged["qty_x"], merged["qty_y"], rtol=0.01)
        
        # Count unmatched
        # Total rows before qty filter minus total rows after
        # But we need to track unmatched_fills count globaly
        # The original code incremented unmatched_fills for every row failure
        
        valid_merged = merged[qty_match].copy()
        
        # Unmatched count logic from original:
        # iterate merged: if isna(signal_ts) -> unmatched. 
        # But we dropped dropna. So before dropna, count how many were NA?
        # merge_asof keeps left rows. if no match, signal_ts is NaN.
        # So len(merged_original) - len(merged_dropna) is unmatched by timestamp?
        # Actually in original code:
        # if pd.isna(row["signal_ts"]): unmatched_fills += 1
        # if not np.isclose: unmatched_fills += 1
        
        # Let's do it cleanly:
        # 1. Total rows for this (sym, side)
        # 2. Rows with NaN signal -> unmatched
        # 3. Rows with valid signal but bad qty -> unmatched
        # 4. Rows with valid signal AND good qty -> matched
        
        # Original merged (before dropna) is what we need to account for
        # Wait, the code above `merged = pd.merge_asof(...)` returns all f_subset rows
        
        # Let's act on `merged` directly
        
        # 1. Identify NaN signals
        nan_mask = merged["signal_ts"].isna()
        n_nan = nan_mask.sum()
        unmatched_fills += n_nan
        
        # 2. Identify Valid Signals but Bad Qty
        # We only check qty on rows where signal is NOT NaN
        # Fill NaN qty_y with -999 to ensure no match if needed, or just slice
        
        valid_sig_mask = ~nan_mask
        if valid_sig_mask.sum() > 0:
             # Vectorized isclose
             # merged.loc[valid_sig_mask, "qty_x"]
             q_x = merged.loc[valid_sig_mask, "qty_x"]
             q_y = merged.loc[valid_sig_mask, "qty_y"]
             
             qty_mismatch_mask = ~np.isclose(q_x, q_y, rtol=0.01)
             n_qty_mismatch = qty_mismatch_mask.sum()
             unmatched_fills += n_qty_mismatch
             
             # 3. Matched = Valid Signal AND Good Qty
             final_match_mask = valid_sig_mask & (~nan_mask) # redundant but clear
             # Actually, we need indices where valid_sig is True AND qty_match is True
             
             # Let's construct a boolean mask for the whole df
             # Default False
             is_matched = pd.Series(False, index=merged.index)
             
             # Where valid sig, check qty
             # We can do: is_matched[valid_sig_mask] = np.isclose(...)
             is_matched.loc[valid_sig_mask] = np.isclose(q_x, q_y, rtol=0.01)
             
             matched_rows = merged[is_matched].copy()
             matched_count += len(matched_rows)
             
             if not matched_rows.empty:
                 # Vectorized Calcs
                 # Slippage: (fill - exp) * sign / exp * 10000
                 sign = 1 if str(side).upper() == "BUY" else -1
                 
                 fill_p = matched_rows["fill_price"]
                 exp_p = matched_rows["expected_price"]
                 
                 slippage_bps = (fill_p - exp_p) * sign / exp_p * 10000.0
                 
                 # Latency
                 latency = (matched_rows["fill_ts"] - matched_rows["signal_ts"]).dt.total_seconds()
                 
                 # Fee Impact
                 # Handle fee_x / fee difference
                 f_col = "fee_x" if "fee_x" in matched_rows.columns else "fee"
                 if f_col in matched_rows.columns:
                     f_fee = matched_rows[f_col].fillna(0.0)
                 else:
                     f_fee = pd.Series(0.0, index=matched_rows.index)
                 
                 # Logic for s_fee: try model_fee_y, then model_fee
                 if "model_fee_y" in matched_rows.columns:
                     s_fee = matched_rows["model_fee_y"]
                 elif "model_fee" in matched_rows.columns:
                     s_fee = matched_rows["model_fee"]
                 else:
                     s_fee = pd.Series(0.0, index=matched_rows.index)
                 
                 s_fee = s_fee.fillna(0.0)
                 fee_imp = f_fee - s_fee
                 
                 # Construct Result DF
                 batch_res = pd.DataFrame({
                     "symbol": sym,
                     "side": side,
                     "fill_ts": matched_rows["fill_ts"].dt.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                     "signal_ts": matched_rows["signal_ts"].dt.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                     "slippage_bps": slippage_bps,
                     "latency_sec": latency,
                     "fee_impact": fee_imp
                 })
                 
                 results.extend(batch_res.to_dict("records"))
        else:
            # All were NaN
            pass

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
