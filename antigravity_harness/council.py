import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from antigravity_harness.catalog import STRATEGY_CATALOG
from antigravity_harness.paths import CERT_DIR
from antigravity_harness.utils import safe_to_csv


def to_md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return " (Empty) "
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join([str(x) for x in r]) + " |")
    return "\n".join([header, sep] + rows)


def run_council_sweep(  # noqa: PLR0915
    symbols: str = "BTC-USD,ETH-USD,SOL-USD",
    timeframes: str = "4h,6h,8h,12h,1d",
    allow_quarantined: bool = False,
    outdir: Optional[str] = None,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    sweep_root = Path(outdir) if outdir else CERT_DIR / "SWEEPS" / f"COUNCIL_CRYPTO_{timestamp}"

    sweep_root.mkdir(parents=True, exist_ok=True)

    print("🦅 COUNCIL SWEEP PROTOCOL INITIATED")
    print(f"   Target: {sweep_root}")

    # 1. Discover Strategies
    strats = [s.name for s in STRATEGY_CATALOG.values() if s.tier in [1, 2] and not s.is_quarantined]
    if allow_quarantined:
        q_strats = [s.name for s in STRATEGY_CATALOG.values() if s.is_quarantined]
        strats.extend(q_strats)
        print("   ⚠️  OVERRIDE: Including Quarantined Strategies")

    print(f"   Strategies: {', '.join(strats)}")

    # 2. Execution Loop
    all_summary_rows = []

    for strat in strats:
        print(f"🔭 POPULATING MATRIX: {strat}")
        sub_out = sweep_root / strat

        cmd = [
            sys.executable,
            "-m",
            "antigravity_harness.cli",
            "certify-sweep",
            "--symbols",
            symbols,
            "--timeframes",
            timeframes,
            "--strategy",
            strat,
            "--gate-profile",
            "crypto_profit",
            "--lookback-days",
            "730",
            "--outdir",
            str(sub_out),
        ]
        if allow_quarantined:
            cmd.append("--allow-quarantined")

        try:
            subprocess.run(cmd, check=True)
            # Load results
            res_path = sub_out / "sweep_results.csv"
            if res_path.exists():
                df = pd.read_csv(res_path)
                if "strategy" not in df.columns:
                    df["strategy"] = strat
                all_summary_rows.append(df)
        except Exception as e:
            print(f"   ❌ Failed to sweep {strat}: {e}")

    # 3. Aggregation
    if not all_summary_rows:
        print("❌ No candidates found.")
        # Minimal brief
        with open(sweep_root / "COUNCIL_BRIEF.md", "w") as f:
            f.write("# Council Sweep Brief\n\nNo candidates found in this run.\n")
        return

    full_df = pd.concat(all_summary_rows, ignore_index=True)
    safe_to_csv(full_df, sweep_root / "sweep_results.csv", index=False)

    # Failure Breakdown
    breakdown = pd.DataFrame(columns=["reason", "count"])
    if "cert_reasons" in full_df.columns:
        fails = full_df[full_df["cert_status"] == "FAIL"]
        reasons = []
        for r in fails["cert_reasons"].dropna():
            reasons.extend([x.strip() for x in str(r).split(";") if x.strip()])
        if reasons:
            breakdown = pd.Series(reasons).value_counts().reset_index()
            breakdown.columns = ["reason", "count"]
            safe_to_csv(breakdown, sweep_root / "failure_breakdown.csv", index=False)

    # Top 10
    def status_score(s: str) -> int:
        if s == "PASS":
            return 2
        if s == "WARN":
            return 1
        return 0

    full_df["s_score"] = full_df["cert_status"].apply(status_score)
    full_df["pf_safe"] = pd.to_numeric(full_df["profit_factor"], errors="coerce").fillna(0)
    full_df["pr_safe"] = pd.to_numeric(full_df["pass_ratio"], errors="coerce").fillna(0)

    top_10 = full_df.sort_values(by=["s_score", "pr_safe", "pf_safe"], ascending=[False, False, False]).head(10)
    cols_display = ["strategy", "symbol", "timeframe", "cert_status", "pr_safe", "pf_safe", "max_dd_pct"]
    cols_display = [c for c in cols_display if c in top_10.columns]

    with open(sweep_root / "COUNCIL_BRIEF.md", "w") as f:
        f.write("# Council Sweep Brief\n\n")
        f.write(f"**Run ID**: {sweep_root.name}\n")
        f.write(f"**Timestamp**: {datetime.now(timezone.utc).isoformat()}Z\n")
        f.write(f"**Quarantine Allowed**: {'YES' if allow_quarantined else 'NO'}\n\n")

        f.write("## 🏆 Top 10 Candidates\n")
        f.write(to_md_table(top_10[cols_display]))
        f.write("\n\n")

        f.write("## ⚠️ Failure Intelligence (Top 5)\n")
        f.write(to_md_table(breakdown.head(5)))
        f.write("\n\n")

        f.write(
            "> 0 PASS does NOT prove no edge. It proves no edge among tested families under current gates + consistency.\n"  # noqa: E501
        )

    print(f"✅ COUNCIL SWEEP COMPLETE: {sweep_root}")
