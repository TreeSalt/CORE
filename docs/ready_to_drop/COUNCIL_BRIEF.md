# COUNCIL BRIEF — TRADER_OPS Sovereign Audit

> **Version**: See `COUNCIL_CANON.yaml` → `repo.version`
> **Status**: **OPERATIONAL — STRICT MODE ENFORCED**

## What Changed (Cumulative from v4.3.4 → Current)

### 1. Fiduciary Chain (Sovereignty)
- **RUN_LEDGER** now cryptographically binds code zip + evidence zip + drop zip with SHA-256
- **CERTIFICATE.json** signed with Ed25519 (`sovereign.key/sovereign.pub`)
- **RUN_LEDGER** is now signed: `RUN_LEDGER_v{VERSION}.json.sig`
- **Drop packet contains self-auditor**: `drop_auditor.py` (standalone, no imports)
- Only **versioned sidecars** (`DROP_PACKET_SHA256_v{VERSION}.txt`) are produced; unversioned sidecars are deleted

### 2. Strict Mode (Fail-Closed)
- `STRICT_MODE=1` is default for all builds
- Dirty git tree → build aborts
- Version mismatch (code vs canon) → build aborts
- Evidence version drift → build aborts
- All verification scripts enforce `--strict`

### 3. Runtime Resilience
- `FlightRecorder` singleton for centralized error/recovery logging
- `SovereignRunner.run_simulation()` returns FAIL instead of crashing
- `_safe_run()` CLI wrapper catches all unhandled exceptions
- NaN/zero-volume data integrity guards in gate evaluation
- `ensure_dirs()` auto-heals file-blocking-dir attacks

### 4. Portfolio API Consistency
- `run_portfolio_backtest` is the single canonical function
- CLI supports `--prices-csv <path>` for fully offline backtesting
- Regime physics uses scale-invariant returns-based basket

### 5. Evidence Smoke Test
- Forge forces evidence regeneration on every build
- Produces `results.csv` (one-row, machine-friendly summary)
- `EVIDENCE_MANIFEST.json` + `DATA_MANIFEST.json` with Merkle roots

## What Did NOT Change
- Gate thresholds (untouched)
- Strategy logic (untouched)
- Certification semantics (untouched)
- Safety overlay DD thresholds (untouched)

## Verification (One Command)
```bash
make verify
```
