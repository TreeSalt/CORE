# MISSION: Implement Zoo Variant ZOO_E1_002 — MEAN_REVERSION_SNIPER
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E1_002
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Implement the MEAN_REVERSION_SNIPER strategy as a certified strategy class conforming to
the mantis_core strategy base contract.

## BLUEPRINT
## ZOO_E1_002 — MEAN_REVERSION_SNIPER

**STRATEGY_ID:** ZOO_E1_002
**CORE_LOGIC:** Intraday mean reversion on overextended moves.
Compute 50-period VWAP on 5m bars. Enter long when price is more than 1.5
standard deviations BELOW VWAP AND RSI(14) < 35 (double confirmation of
oversold). Exit when price returns to VWAP (full mean reversion) OR when
RSI(14) > 55 (momentum exhaustion signal). Hard stop: if price extends
further to 2.5 standard deviations below VWAP, exit immediately — the
mean is broken, not reverting.
**TIMEFRAME:** 5m (VWAP resets daily — critical for no_overnight alignment)
**REGIME_AFFINITY:** Range-bound, mean-reverting intraday — explicitly
designed for days when the market is NOT trending.
**DRAWDOWN_DEFENSE:**
1. Double entry confirmation (VWAP deviation + RSI) prevents chasing
2. 2.5 std dev hard stop — mean reversion thesis invalidated, exit fast
3. VWAP resets daily so no_overnight=True is architecturally coherent
4. RSI exit at 55 (not overbought) — takes profit before reversal risk
**VOLATILITY_DRAG_MITIGATION:** Mean reversion by definition captures
spread rather than riding momentum — lower volatility drag than trend
strategies. Std dev bands auto-scale to current vol regime.
**ANTI_FRAGILITY_SCORE:** 7/10 — performs best in choppy markets that
destroy ZOO_E1_001. Complementary to VOLATILITY_GATEKEEPER — together
they cover both trending and ranging regimes.
**EXPECTED_SHARPE:** 0.90
**EXPECTED_SORTINO:** 1.10
**GRAVEYARD_AVOIDANCE:** VWAP is a native price/volume calculation — no
external data dependency. RSI is stdlib indicator. No import hallucination
risk. Avoids the websocket.SSLOpt pattern documented in GRAVEYARD.md.


## PHYSICS ENGINE CONSTRAINTS (HARD — non-negotiable)
- allow_fractional_shares=False (MES)
- max_contracts=1
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES 5m bars
- Inherit from: mantis_core/strategies/base.py BaseStrategy

## DELIVERABLE
A complete Python strategy file at:
mantis_core/strategies/lab/v_zoo_E1_002_mean_reversion_sniper/v_zoo_E1_002_mean_reversion_sniper.py

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
