# ANTIGRAVITY HARNESS v4.4.42 (OMEGA SOVEREIGN)

**Status**: OMEGA IMMORTAL (v4.4.42)
**Objective**: Absolute, bit-perfect trading strategy sovereignty.

## 🐉 Sovereign Build Protocol
The TRADER_OPS build is protected by **12 Institutional Gates**. It is bit-perfect, deterministic, and eternally verifiable.
See [SOVEREIGN_PROTOCOL.md](docs/SOVEREIGN_PROTOCOL.md) for the full audit specification.

## 🏆 Certification Verdict System

The harness generates a **Certification Bundle** with a rigorous verdict:

*   **PASS**: Strategy meets ALL profit and safety gates on ALL tested symbols.
*   **WARN**: Strategy meets profit gates but triggers minor safety warnings (e.g., higher drawdown but within tolerance).
*   **FAIL**: Strategy fails critical gates (drawdown, profit factor, or consistency) OR infrastructure integrity checks.

### One-Command Proof (Task 4.1)

To certify a strategy (e.g., `v032_simple`) on `BTC-USD` and `ETH-USD` (4h):

```bash
python -m antigravity_harness.cli certify-run \
  --symbols BTC-USD,ETH-USD \
  --timeframes 4h \
  --gate-profile crypto_profit \
  --strategy v032_simple \
  --outdir reports/certification/v4.3.4_proof
```

**Verify the Bundle:**
```bash
python -m antigravity_harness.cli verify-cert-bundle --manifest reports/certification/v4.3.4_proof/MANIFEST.json
```

**Output**: A folder containing `MANIFEST.json`. This file includes:
- `cert_status`: The verdict.
- `cert_reasons`: Why it failed (if applicable).
- `artifact_hashes`: SHA256 hashes of all files in the bundle (including snapshots).
- `manifest_sha256`: SHA256 signature of the manifest itself.
- `trader_ops_version`: The code version used (e.g. 4.x.x).

## 📚 Strategy Catalog

View the available strategies and their Tiers:

```bash
python -m antigravity_harness.cli list-strategies
```

- **Tier 1 (Trend)**: High potential, regime-sensitive (e.g. `v050_trend_momentum`, `v070_donchian_breakout`).
- **Tier 2 (Robust)**: Defensive, guarded strategies (e.g. `v040_alpha_prime`, `v080_volatility_guard_trend`).
- **Baseline**: Reference/Regression strategies (e.g. `v032_simple`).

## 🧹 Strategy Discovery Sweep (Profit Path)

To systematically search for a passing configuration:

```bash
python -m antigravity_harness.cli certify-sweep \
  --strategy v050_trend_momentum \
  --symbols BTC-USD,ETH-USD \
  --timeframes 4h,1d \
  --gate-profile crypto_profit \
  --config-grid grids/v033_smart_sweep.yaml \
  --outdir reports/certification/SWEEPS/PHASE3 \
  --lookback-days 600
```

### 🏛️ Institutional Council Sweep
Standardized dynamic discovery of Tier 1 + 2 strategies:
```bash
python -m antigravity_harness.cli council-sweep
```

## 🛠️ Operational Excellence (Institutional Rails)

### 1. Environment Requirements
- **Python**: 3.10+ (Tested on 3.10 & 3.11)
- **Installation**:
```bash
pip install -r requirements-lock.txt
```

### 2. Preflight & QA
Run the institutional audit gate:
```bash
python3 scripts/preflight.py --auto-clean --qa
```

### 3. Distribution Entrypoint
The canonical way to ship a clean release:
```bash
make build
```
Or directly:
```bash
python3 scripts/make_drop_packet.py --out-dir dist/
```
Output includes a verified zip and a `.sha256` checksum.

## 🛡️ Integrity Rules

1.  **Immutable Snapshots**: All runs use frozen CSV snapshots, never live data, ensuring reproducibility.
2.  **Tamper Evidence**: If you modify any file in a bundle, re-running verification (via hashes) will fail.
3.  **Strict Status**: No "soft passes". A FAIL is a FAIL.

---
---
*Built by Antigravity Harness (v4.4.42)*

## 📂 Documentation (Institutional Gold)
- [Vision: Event Horizon (Option Trading)](docs/vision_event_horizon.md)
- [Roadmap v5.0 (The Titan Upgrade)](docs/roadmap_v5_0.md)
- [Final Readiness Report (READY-TO-DROP)](docs/ready_to_drop/READY_TO_DROP.md)
