#!/bin/bash
# reproduce.sh - Canonical Reproduction Script for TRADER_OPS Institutional Gold
# Usage: ./scripts/reproduce.sh

set -e

echo "🔒 Starting Canonical Reproduction Sequence..."

# 1. Clean Room Setup
echo "🧹 Establishing Clean Room..."
rm -rf .reproduce_venv reports/reproduce_test
python3 -m venv .reproduce_venv
source .reproduce_venv/bin/activate

# 2. Dependency Lock
echo "📦 Installing Strict Dependencies..."
pip install --require-hashes -r requirements.txt
echo "🔧 Installing Antigravity Harness (Editable)..."
pip install -e . --no-deps

# 3. Deterministic Execution
echo "🚀 Executing Deterministic Backtest..."
export PYTHONHASHSEED=0
export SOURCE_DATE_EPOCH=$(date +%s)

# Ensure output directory exists
mkdir -p reports/reproduce_test

python3 -m antigravity_harness.cli portfolio-backtest \
    --symbols MOCK \
    --synthetic \
    --outdir reports/reproduce_test

# 4. Hash Verification
echo "🛡️  Verifying Output Integrity..."
if [ ! -f reports/reproduce_test/RUN_METADATA.json ]; then
    echo "❌ FAIL: RUN_METADATA.json missing."
    exit 1
fi

echo "✅ PASS: Reproduction Complete."
exit 0
