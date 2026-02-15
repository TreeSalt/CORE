#!/bin/bash
set -e
echo "Runnning CLI smoke test..."
python3 -m antigravity_harness.cli portfolio-backtest --synthetic --symbols MOCK --outdir smoke_out

echo "Checking artifacts..."
if [ -f "smoke_out/equity_curve.csv" ]; then echo "  [x] equity_curve.csv found"; else echo "  [!] equity_curve.csv MISSING"; exit 1; fi
if [ -f "smoke_out/regime_log_df.csv" ] || [ -f "smoke_out/PORTFOLIO_SUMMARY.json" ]; then echo "  [x] Summary/Log found"; else echo "  [!] Stats MISSING"; exit 1; fi

echo "Smoke test PASS."
