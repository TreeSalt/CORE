#!/bin/bash
set -e
echo "Runnning CLI smoke test..."
python3 -m mantis_core.cli portfolio-backtest --synthetic --symbols MOCK --outdir reports/forge/synthetic_smoke

echo "Checking artifacts..."
if [ -f "reports/forge/synthetic_smoke/equity_curve.csv" ]; then echo "  [x] equity_curve.csv found"; else echo "  [!] equity_curve.csv MISSING"; exit 1; fi
if [ -f "reports/forge/synthetic_smoke/results.csv" ]; then echo "  [x] results.csv found"; else echo "  [!] results.csv MISSING"; exit 1; fi
if [ -f "reports/forge/synthetic_smoke/regime_log_df.csv" ] || [ -f "reports/forge/synthetic_smoke/PORTFOLIO_SUMMARY.json" ]; then echo "  [x] Summary/Log found"; else echo "  [!] Stats MISSING"; exit 1; fi

echo "Smoke test PASS."
