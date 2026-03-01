# TRADER_OPS PHYSICS CONSTANTS
# docs/constitution/PHYSICS.md — READ THIS BEFORE WRITING ANY CODE
# Version: Locked at build time. Do not edit without council authorization.
# Binding: This file is included in MANIFEST.json and the sovereign drop hash.

---

## SECTION 1 — INSTRUMENT SPECIFICATIONS

### MES (Micro E-mini S&P 500 Futures)
```
asset_class:          future
exchange:             CME
tick_size:            0.25  (points)
tick_value:           $1.25  (= 0.25 pts × $5 multiplier)
multiplier:           $5.00 per point
min_lot:              1 contract (INTEGER ONLY — no fractional lots)
fractional:           false
qty_step:             1
price_unit:           ES points (~5,300–7,000 range in 2025–2026)
approx_notional:      price_pts × $5 → ~$26,500 to $35,000 per contract at current prices
margin_required:      true (cash account CANNOT trade this without margin)
viable_on_2k_cash:    false  (int($2,000 / $34,850) = 0 contracts)
expiry_schedule:      March (H), June (M), September (U), December (Z)
current_front:        MESH6 (expires third Friday March 2026 ≈ 2026-03-21)
next_front:           MESM6
roll_required_by:     2026-03-15 (5 trading days before expiry)
commission_model:     futures_per_contract
commission_usd:       approximately $0.85 per contract per side
session_hours_et:     RTH 09:30–16:00 (78 bars at 5m)
ibkr_extended_hours:  some pre/post market → ~90 bars/day observed in tape
tick_grid_check:      k = round(price / 0.25); assert abs(price - k * 0.25) <= 1e-6
```

### SPY (SPDR S&P 500 ETF Trust)
```
asset_class:          etf
exchange:             NYSE Arca
tick_size:            0.01  (dollars, penny increments)
multiplier:           1.0  (equity — no multiplier)
min_lot:              1 share (fractional allowed on Robinhood)
fractional:           true  (on Robinhood)
qty_step:             0.000001  (Robinhood fractional minimum)
price_unit:           USD (~$560–$620 range in early 2026)
approx_notional:      price × shares_held
margin_required:      false (cash account can hold this)
viable_on_2k_cash:    true  (int($2,000 / $580) = 3 whole shares; fractional allows more)
commission_model:     equity_per_share OR equity_tiered OR zero_commission
commission_usd:       $0 on Robinhood; $0.005/share on IBKR tiered
session_hours_et:     RTH 09:30–16:00 (78 bars at 5m)
tick_grid_check:      k = round(price / 0.01); assert abs(price - k * 0.01) <= 1e-6
IMPORTANT:            SPY price range is $560–$620. If you see a fill at $593 labeled as
                      MES, that is a Frankenstein Fill. MES prices in 2026 are ~5,300–7,000 pts.
```

### QQQ (Invesco QQQ Trust)
```
asset_class:          etf
tick_size:            0.01
multiplier:           1.0
fractional:           true  (on Robinhood)
price_range_2026:     ~$460–$540
viable_on_2k_cash:    true
commission_model:     same as SPY
```

### IWM (iShares Russell 2000 ETF)
```
asset_class:          etf
tick_size:            0.01
multiplier:           1.0
fractional:           true
price_range_2026:     ~$200–$240
viable_on_2k_cash:    true
```

### NVDA (NVIDIA Corporation)
```
asset_class:          equity
tick_size:            0.01
multiplier:           1.0
fractional:           true  (on Robinhood)
price_range_2026:     ~$120–$160
viable_on_2k_cash:    true
```

### BTC (Bitcoin)
```
asset_class:          crypto
exchange:             Robinhood Crypto
tick_size:            0.01  (USD)
multiplier:           1.0
fractional:           true  (Robinhood minimum: ~$1 or 0.000001 BTC)
price_range_2026:     ~$80,000–$105,000 per BTC
viable_on_2k_cash:    true  (fractional trading — buy $1 worth)
commission_model:     robinhood_crypto_spread (embedded in spread, no explicit commission)
broker_required:      Robinhood (IBKR does not support crypto in this account)
```

---

## SECTION 2 — ANNUALIZATION PHYSICS
```
WRONG:  periods_per_year = 252 × 78  = 19,656  (NYSE equity 9:30–4pm at 5m)
RIGHT:  periods_per_year = 252 × observed_bars_per_day

How to compute observed_bars_per_day:
  bars_per_day = len(df) / len(df.index.normalize().unique())
  periods_per_year = 252 * round(bars_per_day)

IBKR MES RTH tape (observed): ~90 bars/day → periods_per_year ≈ 22,680
SPY standard RTH (NYSE):       78 bars/day → periods_per_year = 19,656
IBKR with extended:            90–100 bars/day → periods_per_year = 22,680–25,200

Sharpe ratio scales as sqrt(periods_per_year).
Using wrong periods inflates or deflates Sharpe by sqrt(22680/19656) = 1.074.
On Sharpe=51 this means the correct value might be ~53. Still a hallucination.
The real problem is not the annualization — it is the 1-trade sample size.
```

---

## SECTION 3 — CAPITAL PHYSICS
```
Account: IBKR cash account
Starting capital: $2,000 USD
Margin: NOT enabled
Fractional shares: UNKNOWN (not confirmed for IBKR — use Robinhood for fractional)

INSTRUMENT VIABILITY TABLE (at $2,000 cash, no margin):
  MES:   int($2,000 / ($6,970 × $5)) = int(0.0574) = 0  → BLOCKED: INSUFFICIENT_CAPITAL_MIN_UNIT
  SPY:   int($2,000 / $580) = 3 whole shares              → VIABLE (whole shares)
         $2,000 / $580 = 3.45 fractional shares           → VIABLE (Robinhood fractional)
  QQQ:   int($2,000 / $490) = 4 whole shares              → VIABLE
  IWM:   int($2,000 / $220) = 9 whole shares              → VIABLE
  NVDA:  int($2,000 / $140) = 14 whole shares             → VIABLE
  BTC:   $2,000 / $95,000 = 0.021 BTC                    → VIABLE (Robinhood fractional)

EXECUTION VENUES:
  IBKR:       Role = data_and_research. Equities + ETFs + futures (margin required for MES).
  Robinhood:  Role = execution_stub. Equities + ETFs (fractional) + crypto + options/spreads.

Capital math shorthand: int(capital / notional_per_unit)
If result is 0: emit NO_TRADE_REPORT.json with primary_cause = INSUFFICIENT_CAPITAL_MIN_UNIT.
```

---

## SECTION 4 — FLOAT ARITHMETIC SAFETY
```python
# WRONG — do not use:
assert fill_price % tick_size == 0  # Fails on valid SPY fills due to float representation

# CORRECT — always use this pattern:
import math
def on_tick_grid(price: float, tick_size: float, abs_tol: float = 1e-6) -> bool:
    k = round(price / tick_size)
    return math.isclose(price, k * tick_size, abs_tol=abs_tol)

# For deterministic Decimal-based tick checking:
from decimal import Decimal
def on_tick_grid_decimal(price: float, tick_size: float) -> bool:
    d_price = Decimal(str(price))
    d_tick = Decimal(str(tick_size))
    return (d_price % d_tick) == Decimal('0')

# Validation examples:
# SPY:  on_tick_grid(593.01, 0.01)  → True  ✓
# SPY:  on_tick_grid(593.0345, 0.01) → False ✓  (off-grid price — slippage exceeds tick)
# MES:  on_tick_grid(5300.25, 0.25)  → True  ✓
# MES:  on_tick_grid(593.0, 0.25)    → True  (WRONG PHYSICS — 593 is SPY price, not MES points)
#       → This is why tick_size must come from InstrumentSpec.symbol, not a default

# Python float trap demonstration:
# 0.01 + 0.02 = 0.030000000000000002  (not 0.03)
# 593.01 % 0.01 = 0.009999999999987... (not 0.0)
# Always use isclose or Decimal for financial tick math.
```

---

## SECTION 5 — STATISTICAL POWER THRESHOLDS
```
Minimum for statistically meaningful Profit Factor:   30 round-trip trades
Minimum for statistically meaningful Sharpe ratio:    30 independent observations
Minimum for OOS strategy promotion:                   60+ trading days of OOS data

Current IBKR tape total length:   ~44 trading days (Jan 8 – Feb 20, 2026)
80/20 IS/OOS split on 44 days:    35 days IS, 9 days OOS (~702 bars)
9 days of OOS at 1 trade / 3 days:   ~3 OOS trades

CONCLUSION: Current tape is insufficient for OOS strategy promotion decisions.
Use the harness for infrastructure validation only. Do not promote strategies.
Minimum required for meaningful OOS: 6+ months of real data.

LOW-SAMPLE GATE THRESHOLDS (enforced by Patch E):
  round_trip_trades < 20 OR fills_count < 30 OR sessions < 10:
    → metrics_valid = false
    → metrics_invalid_reason = "LOW_SAMPLE"
    → append SMOKE_LOW_SAMPLE to status
    → these results CANNOT be used for strategy certification or alpha claims

SHARPE REALITY CHECK:
  Best systematic equity strategies: Sharpe 1.5–3.0 (annual)
  Top quantitative hedge funds:      Sharpe 2.0–5.0
  Physically impossible:             Sharpe > 10 on any real strategy over real data
  Frankenstein artifact:             Sharpe > 10 on < 30 fills
```

---

## SECTION 6 — CONTRACT CALENDAR (CRITICAL — MESH6 EXPIRES SOON)
```
As of 2026-02-24:
  Active front-month: MESH6 (March 2026 contract)
  Expiry date:        2026-03-21 (third Friday of March 2026)
  Days until expiry:  25 trading days from 2026-02-24
  Roll recommendation: Begin rolling to MESM6 by 2026-03-13 (5 days before expiry)

  Historical tape in repo: data/ibkr/mes_5m_ibkr_rth.csv
  All tape data is MESH6. After roll, new data is MESM6.
  These are different contracts with different prices.
  Do NOT concatenate MESH6 and MESM6 data without a continuous contract adjustment.

PANAMA ROLL METHOD (NOT_IMPLEMENTED):
  Panama back-adjustment requires full historical prices of both contracts at roll time.
  Cannot be computed on a forward-only data stream.
  The roll_method: "panama" field in instrument_specs.json is a structural stub only.
  Until implemented: do not claim continuous contract data is comparable pre/post roll.

MESH6 roll to MESM6 STOP CONDITION:
  If the forward data collector detects a new front-month contract without a validated
  roll specification: stop collection and emit BLOCKED_CONTRACT_ROLL_NOT_CONFIGURED.

UNADJUSTED SPLICING PROHIBITION (MISSION v4.5.424):
  Do NOT concatenate MESH6 and MESM6 data (or any two contracts) without a continuous contract adjustment 
  (e.g., Panama or Proportional). Unadjusted splicing creates false volatility spikes at roll time 
  that destroy Sharpe ratios and invalidate all statistical risk metrics.
```

## 3. CASH ACCOUNT CONSTRAINT
**CASH ACCOUNT CONSTRAINT**: Cash accounts cannot hold short positions. 
Any `target_weight < 0` or `OrderSide.SELL` to open on a cash profile must fail closed with reason code: `CANNOT_SHORT_CASH_ACCOUNT`.
This is a physical law of the TRADER_OPS treasury layer.
