#!/bin/bash
set -euo pipefail

# Vanguard Workflow Consolidation (v4.3.1) - Council Sweep Protocol
# Standardized Crypto Search: BTC/ETH/SOL on 4h-1d scales.

# 1. Setup Timestamp & Dir
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S_%6N")
OUTDIR="reports/certification/SWEEPS/COUNCIL_CRYPTO_${TIMESTAMP}"
mkdir -p "$OUTDIR"

echo "🦅 COUNCIL SWEEP PROTOCOL INITIATED"
echo "   Target: $OUTDIR"
echo "   Timestamp: $TIMESTAMP"

# 2. Extract Strategy List (Dynamic from Catalog)
STRATS=$(python3 -c "from antigravity_harness.catalog import STRATEGY_CATALOG; print(' '.join([s.name for s in STRATEGY_CATALOG.values() if s.tier in [1, 2] and not s.is_quarantined]))")

# Add Quarantined if override requested? 
# ALLOW_QUARANTINED defaults to 0.
ALLOW_QUARANTINED=${ALLOW_QUARANTINED:-0}
if [ "$ALLOW_QUARANTINED" -eq "1" ]; then
    echo "   ⚠️  OVERRIDE: Including Quarantined Strategies"
    STRATS_Q=$(python3 -c "from antigravity_harness.catalog import STRATEGY_CATALOG; print(' '.join([s.name for s in STRATEGY_CATALOG.values() if s.is_quarantined]))")
    STRATS="$STRATS $STRATS_Q"
fi

echo "   Strategies: $STRATS"

# 3. Execution Loop
echo "---------------------------------------------------"
for STRAT in $STRATS; do
    echo "🔭 POPULATING MATRIX: $STRAT"
    
    SUBDIR="$OUTDIR/$STRAT"
    
    # Task 2: Quarantine Integrity - only pass --allow-quarantined if env var set
    CMD="python3 -m antigravity_harness.cli certify-sweep \
        --symbols BTC-USD,ETH-USD,SOL-USD \
        --timeframes 4h,6h,8h,12h,1d \
        --strategy $STRAT \
        --gate-profile crypto_profit \
        --lookback-days 730 \
        --outdir $SUBDIR"
    
    if [ "$ALLOW_QUARANTINED" -eq "1" ]; then
        CMD="$CMD --allow-quarantined"
    fi
    
    $CMD || echo "   ❌ Failed to sweep $STRAT (continuing...)"

done
echo "---------------------------------------------------"

# 4. Aggregation (Python)
# Task 1: Fix aggregation logic & Remove to_markdown dependency
cat <<EOF > "$OUTDIR/aggregate.py"
import os
import pandas as pd
from datetime import datetime
import sys

outdir = "$OUTDIR"
quarantine_allowed = "$ALLOW_QUARANTINED" == "1"
all_rows = []

# Walk subdirectories and find sweep_results.csv from each strategy
for root, dirs, files in os.walk(outdir):
    for f in files:
        if f == "sweep_results.csv" and root != outdir:
            path = os.path.join(root, f)
            try:
                df = pd.read_csv(path)
                # Add Strategy Name if missing (from folder name)
                if "strategy" not in df.columns:
                     strat_name = os.path.basename(root)
                     df["strategy"] = strat_name
                all_rows.append(df)
            except Exception as e:
                print(f"Skipping {path}: {e}")

if not all_rows:
    print("❌ No sweep results found for aggregation.")
    sys.exit(0)

full_df = pd.concat(all_rows, ignore_index=True)
full_df.to_csv(os.path.join(outdir, "sweep_results.csv"), index=False)

# Failure Breakdown
# Task 1: Use cert_status/cert_reasons
if "cert_reasons" in full_df.columns:
    fails = full_df[full_df["cert_status"] == "FAIL"]
    # Parse cert_reasons (comma separated)
    all_reasons = []
    for r in fails["cert_reasons"].dropna():
        all_reasons.extend([x.strip() for x in str(r).split(";") if x.strip()])
    
    if all_reasons:
        breakdown = pd.Series(all_reasons).value_counts().reset_index()
        breakdown.columns = ["reason", "count"]
        breakdown.to_csv(os.path.join(outdir, "failure_breakdown.csv"), index=False)
    else:
        breakdown = pd.DataFrame(columns=["reason", "count"])
else:
    breakdown = pd.DataFrame(columns=["reason", "count"])

# Manual Table Generator (to avoid tabulate dep)
def to_md_table(df):
    if df.empty: return " (Empty) "
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join([str(x) for x in r]) + " |")
    return "\n".join([header, sep] + rows)

# Top 10 Candidates (Task 1: Use correct columns)
def status_score(s):
    if s == "PASS": return 2
    if s == "WARN": return 1
    return 0

full_df["s_score"] = full_df["cert_status"].apply(status_score)
full_df["pf_safe"] = pd.to_numeric(full_df["profit_factor"], errors="coerce").fillna(0)
full_df["pr_safe"] = pd.to_numeric(full_df["pass_ratio"], errors="coerce").fillna(0)

# Sort: Status -> Pass Ratio -> PF
top_10 = full_df.sort_values(by=["s_score", "pr_safe", "pf_safe"], ascending=[False, False, False]).head(10)

# Select relevant columns for display
cols_display = ["strategy", "symbol", "timeframe", "cert_status", "pr_safe", "pf_safe", "max_dd_pct"]
cols_display = [c for c in cols_display if c in top_10.columns]
top_10_display = top_10[cols_display]

with open(os.path.join(outdir, "COUNCIL_BRIEF.md"), "w") as f:
    f.write(f"# Council Sweep Brief\n\n")
    f.write(f"**Run ID**: {os.path.basename(outdir)}\n")
    f.write(f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n")
    f.write(f"**Profile**: crypto_profit\n")
    f.write(f"**Quarantine Allowed**: {'YES' if quarantine_allowed else 'NO'}\n\n")
    
    f.write("## 🏆 Top 10 Candidates\n")
    f.write(to_md_table(top_10_display))
    f.write("\n\n")
    
    f.write("## ⚠️ Failure Intelligence (Top 5)\n")
    f.write(to_md_table(breakdown.head(5)))
    f.write("\n\n")
    
    f.write("> 0 PASS does NOT prove no edge. It proves no edge among tested families under current gates + consistency.\n")

# Use python to print absolute path for clarity
python3 -c "import os; print(f'✅ Aggregation Complete. Brief available at {os.path.abspath(\"$OUTDIR\")}/COUNCIL_BRIEF.md')"
EOF

python3 "$OUTDIR/aggregate.py"

echo "✅ COUNCIL SWEEP COMPLETE"
echo "   Output: $OUTDIR"
