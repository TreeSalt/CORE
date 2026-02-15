# READY-TO-DROP: TRADER_OPS v4.3.4 (OMEGA SOVEREIGN)

## 1) What This Repo Is
**TRADER_OPS** is the institutional-grade strategy engine and certification harness for the Vanguard Reality trading system. It is protected by the **OMEGA Sovereign Protocol** (12 Institutional Gates).
**Current Status**: **OMEGA IMMORTAL**. The core harness is stable (v4.3.4), bit-perfect, and ready for absolute distribution.

## Builders vs Consumers (Important)
- **Builder (repo workspace)**: `make_drop_packet.py` produces `dist/TRADER_OPS_READY_TO_DROP_v4.3.4.zip`. The `dist/` prefix is a build artifact path, not part of the zip contents. Verify with `sha256sum dist/TRADER_OPS_READY_TO_DROP_v4.3.4.zip` and compare to `docs/ready_to_drop/DROP_PACKET_SHA256.txt`.
- **Consumer (received packet)**: You receive the zip directly (no `dist/` folder inside). Verify using the sidecar `DROP_PACKET_SHA256.txt` provided alongside the zip: `sha256sum TRADER_OPS_READY_TO_DROP_v4.3.4.zip`.

> [!NOTE]
> `PAYLOAD_MANIFEST.json` does not list itself in `file_sha256` to prevent hash recursion; this is intentional and standard.

> [!NOTE]
> Older reports/manifests may reference 4.3.4; do not edit them; new runs will stamp 4.3.4.

## 2) Physics Laws (Non-Negotiables)
1.  **Engine Owns Signal Shifting**: The engine automatically shifts signals by 1 candle to prevent look-ahead bias. Strategies must not shift signals themselves.
2.  **Stops at Fill Price**: Stop losses and take profits are calculated based on the *actual fill price*, not the signal price.
3.  **Gap-Through-Stop Modeled**: If the market gaps through a stop level, the exit is executed at the open of the next bar (slipped), not the stop price.
4.  **Immutable Snapshots**: All Certification Runs MUST use frozen CSV snapshots using `antigravity_harness.data`. Live API calls are forbidden during backtests. Checksums are verified.
5.  **Portfolio t-1 Semantics**: Portfolio regime detection and weight computation use data strictly up to bar `t-1`. Execution occurs at bar `t` prices. This is enforced by `portfolio_engine.py` and verified by anti-lookahead trap tests.

## 3) Status System (PASS/WARN/FAIL)
The system uses a strict 3-state logic. A single FAIL in any component fails the entire run.

*   **profit_status**: Pass/Fail (Is it making money?)
*   **safety_status**: Pass/Warn/Fail (Is it safe?)
*   **overall_status**: The final verdict.

**Truth Table:**

  profit_status  safety_status  => overall_status
  PASS           PASS           => PASS
  PASS           WARN           => WARN
  PASS           FAIL           => FAIL
  FAIL           PASS           => FAIL
  FAIL           WARN           => FAIL
  FAIL           FAIL           => FAIL

**Non-downgradable FAIL Rule**: Any `profit_status=FAIL` OR `safety_status=FAIL` results in an immediate hard stop. No overrides.

## 4) Gate Profiles (Single Source of Truth)
Defined in `antigravity_harness/profiles.py`.

### A) equity_fortress (Strict Safety)
*   **Asset Class**: Equities
*   **Min Profit Factor**: 1.1
*   **Min Sharpe**: 0.5
*   **Min Trades**: 40
*   **Max Drawdown**: >15% (WARN), >20% (FAIL)
*   **Min Volatility**: N/A

### B) crypto_profit (Growth First)
*   **Asset Class**: Crypto
*   **Min Profit Factor**: 1.6
*   **Min Sharpe**: 0.0 (PF is king)
*   **Min Trades**: 40
*   **Max Drawdown**: >25% (WARN), >40% (FAIL)
*   **Min Volatility**: 0.40 (FAIL if < 0.40; "Stablecoin Defense")

**GATE_MISCLASSIFICATION is FAIL**: Applying a crypto profile to a low-volatility asset (or vice versa) results in a hard failure.

## 5) Regime vs Safety Overlay (Clarification)
- **Regime**: Market-state label (e.g. `TREND_LOW_VOL`, `PANIC`). Determines **how** we want to be positioned (Momentum vs Mean Reversion vs Cash). Evaluated at **rebalance cadence** (e.g. Monthly).
- **Safety Overlay**: Portfolio brake (airbags). Reacts to drawdown limits regardless of regime. Evaluated **every bar**. **Phase 9D overlay default = ON for deployment evaluation.**

**Two Distinct Drawdowns:**
- **Basket Drawdown** (regime physics): Scale-invariant; computed from a returns-based basket index (`basket_index[t] = basket_index[t-1] * (1 + mean(asset_returns[t]))`). Used by `regimes.py` for PANIC detection.
- **Portfolio Drawdown** (certification/safety): Computed from the portfolio's actual equity curve. Used by `portfolio_safety_overlay.py` for DD Brake decisions.

## 6) Red-Team Defenses Implemented (Bullet List)
*   **Snapshot Integrity Hashing**: SHA256 verification of input data; run rejected on mismatch.
*   **Walk-Forward Leakage Prevention**: Strict train/test split enforcement in Certification Runs.
*   **Zombie Defense**: (Not yet implemented; pending v5).
*   **Bad Apple Portfolio Rule**: If ANY single strategy/asset pair in a portfolio FAILS, the ENTIRE portfolio FAILS.
*   **WARN Laundering Cap**: If >30% of assets in a portfolio trigger a WARN, the portfolio FAILS.
*   **Empty Portfolio Defense**: A portfolio with 0 trades is a FAIL.
*   **Drift/Consistency Rule**: Strategy must maintain `pass_ratio >= 0.60` across walk-forward windows (Safety Fail).

## 6) Core CLI Commands (Reproducible)

### Tests
```bash
python -m unittest discover tests
# OR
pytest tests/
```

### Preflight (The Institutional Audit)
```bash
python scripts/preflight.py --auto-clean
```

### Clean Repo (Strict verification)
```bash
python scripts/clean_repo.py --verify-strict
```

### Council Sweep (Crypto)
```bash
bash scripts/council_sweep_crypto.sh
```

### Portfolio Backtest (Phase 9 + 9D Safety)
```bash
python -m antigravity_harness.cli portfolio-backtest \
  --symbols BTC-USD,ETH-USD,SOL-USD \
  --start 2021-01-01 --end 2024-12-31 \
  --rebalance M --router regime_v1 \
  --dd_reduce -0.15 --dd_off -0.25 --dd_hard -0.40 \
  --max_weight_per_asset 0.50 --min_positions 2 \
  --outdir reports/portfolio/run_001
```
**Outputs**: `equity_curve.csv`, `regime_log.csv`, `regime_matrix.json`, `PORTFOLIO_SUMMARY.json`, `SUMMARY.md`, `COUNCIL_PORTFOLIO_BRIEF.md`.

**Phase 9D Safety Overlay** (evaluated every bar, not just at rebalance):
- **DD Brake**: RISK_REDUCE at -15%, RISK_OFF at -25%, HARD_FAIL at -40%.
- **Hysteresis**: No severity downgrade (RISK_OFF → RISK_REDUCE forbidden). Recovery requires DD past separate thresholds.
- **Concentration Caps**: Max 50% per asset, min 2 distinct positions.
- **Safety CLI flags**: `--dd_reduce`, `--dd_off`, `--dd_hard`, `--reduce_multiplier`, `--reentry_off`, `--reentry_reduce`, `--max_weight_per_asset`, `--min_positions`, `--enable_shock_overlay`.

### Reality Gap Check (Fixture Test)
```bash
python -m antigravity_harness.cli reality-gap \
  --fills tests/fixtures/fills.csv \
  --signals tests/fixtures/signals.csv \
  --outdir reports/reality_check_final
```

### Package Core
```bash
python scripts/package_core.py
```

## 7) What We Know vs What We Don't
*   **Known Good**: The harness infrastructure (preflight, packaging, sweep pipeline, reality-gap sensor, portfolio regime router) is robust and operational.
*   **Unknown**: Profitable configurations under `crypto_profit`. Recent sweeps yielded 0 candidates due to profit consistency < 60%. We have the tools to find them, but the specific parameters are not yet locked.

## 8) Next Actions (Ordered)
1.  **Run Preflight**: Ensure the jet is airworthy.
2.  **Run Council Sweep**: Execute the standard crypto sweep.
3.  **Run Portfolio Backtest**: Evaluate regime-aware allocation.
4.  **Inspect COUNCIL_BRIEF**: Analyze `reports/certification/PORTFOLIO/COUNCIL_PORTFOLIO_BRIEF.md`.
5.  **Alpha Hunting**: ONLY after the above are confirmed, proceed to Tiered hunting (Strategy work).
