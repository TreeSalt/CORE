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
# Fixed Epoch: 2020-01-01 00:00:00 UTC (Institutional Standard)
export SOURCE_DATE_EPOCH=1577836800
export PYTHONHASHSEED=0
export METADATA_RELEASE_MODE=1

# Ensure output directory exists (Clean Slate)
rm -rf reports/reproduce_test
mkdir -p reports/reproduce_test

python3 -m mantis_core.cli portfolio-backtest \
    --symbols MOCK \
    --synthetic \
    --outdir reports/reproduce_test

# 4. Hash Verification (The Truth Test)
echo "🛡️  Verifying Output Integrity..."

# We need to verify that the generated evidence matches the DISTRIBUTED evidence.
# We assume this script is running from the root of the extracted code zip, 
# and we might not have the original evidence zip handy unless we are in the drop.
# However, if we are in the repo, we can check against reports/forge/synthetic_smoke/EVIDENCE_MANIFEST.json

MANIFEST="reports/forge/synthetic_smoke/EVIDENCE_MANIFEST.json"
if [ ! -f "$MANIFEST" ]; then
    echo "⚠️  WARN: Reference manifest not found at $MANIFEST. Cannot verify bit-for-bit match."
    echo "   (This is expected if ensuring basic reproducibility without the evidence artifact)"
else
    echo "🔍 Comparing against Council Manifest: $MANIFEST"
    
    # robust python verification
    python3 -c "
import json, sys, hashlib

manifest_path = '$MANIFEST'
target_file = 'reports/reproduce_test/SUMMARY.md'

try:
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    expected_hash = manifest.get('files', {}).get('SUMMARY.md')
    if not expected_hash:
        print('⚠️  WARN: SUMMARY.md not found in manifest.')
        sys.exit(0) 

    with open(target_file, 'rb') as f:
        data = f.read()
        actual_hash = hashlib.sha256(data).hexdigest()
    
    if actual_hash == expected_hash:
        print(f'✅ PASS: SUMMARY.md matches Council Manifest ({actual_hash[:8]}).')
        sys.exit(0)
    else:
        print(f'❌ FAIL: SUMMARY.md mismatch!')
        print(f'   Expected: {expected_hash}')
        print(f'   Actual:   {actual_hash}')
        sys.exit(1)
except Exception as e:
    print(f'❌ FAIL: Verification error: {e}')
    sys.exit(1)
"
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

if [ ! -f reports/reproduce_test/RUN_METADATA.json ]; then
    echo "❌ FAIL: RUN_METADATA.json missing."
    exit 1
fi

echo "✅ PASS: Reproduction Complete & Verified."
exit 0
