# READY-TO-DROP: TRADER_OPS (Sovereign Protocol)

> **Current Version**: See `v0.0.0-POISON` → `repo.version`
> **Verification**: `make verify` (fail-closed, strict mode)

## 1) What This Repo Is
**TRADER_OPS** is the institutional-grade strategy engine and certification harness for the Vanguard Reality trading system. It is protected by the **Sovereign Protocol** (12 Institutional Gates + Fiduciary Certificate).

## Builders vs Consumers

- **Builder (repo workspace)**: Run `make all` to produce `dist/TRADER_OPS_READY_TO_DROP_v{VERSION}.zip`. Verify with `make verify`.
- **Consumer (received packet)**: Run `python3 drop_auditor.py TRADER_OPS_READY_TO_DROP_v{VERSION}.zip` (included in drop). Or manually: `sha256sum TRADER_OPS_READY_TO_DROP_v{VERSION}.zip` and compare to `DROP_PACKET_SHA256_v{VERSION}.txt`.

> [!NOTE]
> `PAYLOAD_MANIFEST.json` does not list itself in `file_sha256` to prevent hash recursion; this is intentional and standard.

> [!NOTE]
> Only versioned sidecars (`DROP_PACKET_SHA256_v{VERSION}.txt`) are authoritative. Unversioned sidecars are legacy and should be ignored.

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

### B) crypto_profit (Growth First)
*   **Asset Class**: Crypto
*   **Min Profit Factor**: 1.6
*   **Min Sharpe**: 0.0 (PF is king)
*   **Min Trades**: 40
*   **Max Drawdown**: >25% (WARN), >40% (FAIL)
*   **Min Volatility**: 0.40 (FAIL if < 0.40; "Stablecoin Defense")

**GATE_MISCLASSIFICATION is FAIL**: Applying a crypto profile to a low-volatility asset (or vice versa) results in a hard failure.

## 5) Regime vs Safety Overlay
- **Regime**: Market-state label (e.g. `TREND_LOW_VOL`, `PANIC`). Determines **how** we want to be positioned. Evaluated at **rebalance cadence** (e.g. Monthly).
- **Safety Overlay**: Portfolio brake (airbags). Reacts to drawdown limits regardless of regime. Evaluated **every bar**. **Phase 9D overlay default = ON for deployment evaluation.**

**Two Distinct Drawdowns:**
- **Basket Drawdown** (regime physics): Scale-invariant; computed from a returns-based basket index. Used by `regimes.py` for PANIC detection.
- **Portfolio Drawdown** (certification/safety): Computed from the portfolio's actual equity curve. Used by `portfolio_safety_overlay.py` for DD Brake decisions.

## 6) Verification Commands

### One True Command (Council Audit)
```bash
make verify
# or: bash scripts/one_true_command.sh dist
```

### Full Build + Verify Pipeline
```bash
make all
```

### Tests
```bash
make test
```

### Preflight
```bash
make preflight
```

### Clean
```bash
make clean
```

Run `make help` for the full command reference.

## 7) What We Know vs What We Don't
*   **Known Good**: The harness infrastructure (preflight, packaging, sweep pipeline, reality-gap sensor, portfolio regime router) is robust and operational.
*   **Unknown**: Profitable configurations under `crypto_profit`. Recent sweeps yielded 0 candidates due to profit consistency < 60%. We have the tools to find them, but the specific parameters are not yet locked.

## 8) Claim Scope (Fiduciary)
This certification covers:
- **Artifact integrity**: Cryptographic binding of code + evidence + drop via RUN_LEDGER
- **Signed certification**: Ed25519 certificate + signature
- **Signed ledger**: Ed25519 ledger signature
- **Self-auditing**: Drop contains `drop_auditor.py` for standalone verification
- **Strict mode**: Fail-closed on dirty tree, version mismatch, hash mismatch

This certification does **NOT** claim:
- Live-market profitability
- Real data provenance (only synthetic smoke evidence is certified)
- Forward-looking performance guarantees
