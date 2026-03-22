# MISSION: Implement Zoo Variant ZOO_E1_004 — OPENING_RANGE_BREAKOUT
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E1_004
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Implement the OPENING_RANGE_BREAKOUT strategy as a certified strategy class conforming to
the mantis_core strategy base contract.

## BLUEPRINT
## ZOO_E1_004 — OPENING_RANGE_BREAKOUT

**STRATEGY_ID:** ZOO_E1_004
**CORE_LOGIC:** Classic Opening Range Breakout adapted for MES 5m bars.
Define opening range as the high/low of the first 6 bars after market open
(first 30 minutes). Enter long on a 5m bar close ABOVE opening range high
with volume confirmation (current bar volume > 1.5x average of opening range
bar volumes). Exit at end of day (no_overnight=True enforces this) OR on
a 5m close back inside the opening range (breakout failure). Hard stop:
50% of opening range width below entry.
**TIMEFRAME:** 5m (opening range = bars 1-6 of session)
**REGIME_AFFINITY:** High-conviction directional days — gap-and-go sessions,
FOMC follow-through, earnings-driven index moves. Sits idle on low-conviction
days when opening range is not broken with volume.
**DRAWDOWN_DEFENSE:**
1. Volume confirmation filter eliminates false breakouts (the primary
   cause of ORB drawdown in backtests).
2. Stop at 50% of opening range width — loss is bounded by market
   structure, not arbitrary percentage.
3. Only 1 trade per day (one breakout per session) — max_trades_per_day=3
   constraint means 2 remaining slots unused. Conservative by design.
4. no_overnight=True means all P&L is realized intraday.
**VOLATILITY_DRAG_MITIGATION:** ORB naturally selects high-momentum days.
On low-vol days the range is tight and breakout rarely confirms with volume
— the strategy simply doesn't trade, avoiding the chop entirely.
**ANTI_FRAGILITY_SCORE:** 7/10 — highly regime dependent (underperforms
in directionless markets) but when it fires it fires with conviction. The
volume filter is the anti-fragility mechanism.
**EXPECTED_SHARPE:** 0.88
**EXPECTED_SORTINO:** 1.15
**GRAVEYARD_AVOIDANCE:** All inputs are OHLCV — high, low, close, volume.
Zero external dependencies. Opening range is reset daily — no state
accumulation. No overnight risk by design.


## PHYSICS ENGINE CONSTRAINTS (HARD — non-negotiable)
- allow_fractional_shares=False (MES)
- max_contracts=1
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES 5m bars
- Inherit from: mantis_core/strategies/base.py BaseStrategy

## DELIVERABLE
A complete Python strategy file at:
mantis_core/strategies/lab/v_zoo_E1_004_opening_range_breakout/v_zoo_E1_004_opening_range_breakout.py

The strategy must:
1. Inherit from BaseStrategy
2. Implement generate_signals(bars: pd.DataFrame) -> pd.Series
3. Pass the strategy contract test suite
4. Include docstring with VARIANT, REGIME_AFFINITY, ANTI_FRAGILITY_SCORE

## CONSTRAINTS
- No hardcoded parameters — derive all thresholds dynamically from price data
- No external API calls
- No overnight positions
- Fail closed on any Physics Engine violation
- Output valid Python only
