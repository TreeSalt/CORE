# COUNCIL BRIEF — Phase 9E v2

**Version**: 4.3.4 | **Build Date**: 2026-02-13
**Status**: **OPERATIONAL**
**Latest Milestone**: Sovereign Omega v4.3.4 Lockdown

## What Changed

### 1. Portfolio API Consistency
- `run_portfolio_backtest` is the **single canonical function**. Returns `(portfolio, regime_log, equity_curve_df)`.
- Previous wrapper pattern (`_verbose`) removed — all callers use the same function.
- CLI now supports `--prices-csv <path>` for fully offline backtesting.

### 2. Regime Physics V2 (Scale-Invariant Basket)
- **Before**: Basket drawdown used `mean(raw_prices)` — a $35,000 asset dominated a $150 asset.
- **After**: Uses returns-based `basket_index = cumprod(1 + mean(per_asset_returns)) * 100`. Multiplying any asset by 10x has **zero effect** on drawdown or panic decisions.
- Safety overlay shock trigger also fixed to use per-asset returns.
- New test: `test_basket_scale_invariant.py` (3 assertions).

### 3. Portability Restore
- Drop packet whitelist now includes: `clean_repo.py`, `package_core.py`, `council_sweep_crypto.sh`.
- `TRADER_OPS_READY_TO_DROP_vX.Y.Z.zip` + SHA sidecar copied to engine root.
- No machine-specific absolute paths anywhere.

### 4. Offline Defaults
- CLI errors clearly if neither `--prices-csv` nor `--fetch` is provided.
- No silent network calls.

## What Did NOT Change
- Gate thresholds (untouched)
- Strategy logic (untouched)
- Certification semantics (untouched)
- Safety overlay DD thresholds (untouched)
