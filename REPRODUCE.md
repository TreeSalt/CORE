# Reproducing TRADER_OPS Institutional Gold

This guide provides instructions for verifying the TRADER_OPS build in a "Clean Room" environment.

## Prerequisites

- Python 3.9+
- `make` (optional, for build automation)
- `git`

## Quick Start (One Command)

The `reproduce.sh` script handles virtual environment creation, dependency installation, and verification.

```bash
bash scripts/reproduce.sh
```

## Manual Verification Steps

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Strict Dependencies**:
   ```bash
   pip install --require-hashes -r requirements.txt
   ```

3. **Run Backtest**:
   ```bash
   python3 -m antigravity_harness.cli portfolio-backtest --symbols MOCK --synthetic --outdir reports/verification
   ```

4. **Verify Hash Integrity**:
   Inspect `reports/verification/RUN_METADATA.json` and ensure it matches the console output.

## Troubleshooting

- **Dependency Errors**: Ensure you act using a fresh virtual environment to avoid conflicts with system packages.
- **Timestamp Drift**: The build system enforces UTC. Ensure your system clock is synchronized.
