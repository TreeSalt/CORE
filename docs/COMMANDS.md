# Operator's Command Guide
==========================

This document serves as the single source of truth for all system commands within the TRADER_OPS environment.

## 🚀 Quick Start
Run `make help` for a dynamic cheat-sheet of available targets.
Run `make commands` to view this guide directly in your terminal.

## 🔬 Strategy Execution
The system defaults to **Assisted Mode** (Fail-Closed).

### Assisted Mode (Default)
Generates a `TRADE_PROPOSAL.md` but blocks execution until authorized.
```bash
# Example: Run backtest in assisted mode
python3 -m antigravity_harness.cli portfolio-backtest --symbols MES --strategy v040_alpha_prime
```

### Authorization
To authorize trade execution, append the `--authorize` flag.
```bash
# Example: Authorize trade execution
python3 -m antigravity_harness.cli portfolio-backtest --symbols MES --authorize
```

### Autopilot Mode
Bypasses the proposal gate (Institutional Grade only).
```bash
# Example: Run in autopilot mode
python3 -m antigravity_harness.cli portfolio-backtest --symbols MES --mode autopilot
```

## 🔬 Walk-Forward & Evidence
Generate decoupled In-Sample (IS) and Out-of-Sample (OOS) evidence.

- `python3 scripts/generate_evidence.py --symbols [SYM] --outdir [DIR]`: Runs the walk-forward harness.
- **Example**:
```bash
python3 scripts/generate_evidence.py --symbols MES_5M_IBKR_RTH --outdir reports/wf_v1 --equity
```

## 🩺 Error Management
The system uses **The Archivist** to track, classify, and learn from failures.

- `make show-errors`: Displays the last 20 events from the `ERROR_LEDGER.json`.
- `python3 scripts/archivist.py --log [CAT] [MSG] [GATE]`: Manually log a new incident.
- `python3 scripts/archivist.py --learn [CODE] [SOL]`: Record a new "vaccine" (resolution).

## 🩹 Self-Healing (The Repo Doctor)
If the repository feels "dirty" or files are missing:
- `make heal`: Runs the `self_heal.py` protocol.

## 📦 Build & Release
- `make release`: Executes a clean build followed by a Sovereign Audit.
- `make build`: Forges the drop packet in the `dist/` directory.

## 🛡️ Verification
- `make verify`: Comprehensive end-to-end audit (fail-closed).
- `make zip-verify`: Validates the static integrity of the drop packet.

---
*Identity Warden: sovereign.pub found.*
*Fiduciary State: Institutional Gold (v4.7.25).*
