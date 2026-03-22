# MISSION: Implement Zoo Variant ZOO_E1_003 — REGIME_CHAMELEON
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E1_003
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Implement the REGIME_CHAMELEON strategy as a certified strategy class conforming to
the mantis_core strategy base contract.

## BLUEPRINT
## ZOO_E1_003 — REGIME_CHAMELEON

**STRATEGY_ID:** ZOO_E1_003
**CORE_LOGIC:** Dual-mode strategy that dynamically switches between trend
and mean-reversion based on ADX reading. When ADX(14) > 25 (trending
regime): follow EMA(8)/EMA(21) crossover signals long-only. When ADX(14)
< 20 (ranging regime): use Bollinger Band(20, 2.0) mean reversion — enter
long at lower band, exit at midline. When ADX is between 20-25 (transition
zone): no new entries, manage existing positions only.
**TIMEFRAME:** 5m
**REGIME_AFFINITY:** Universal — explicitly designed to survive regime
transitions that destroy single-mode strategies.
**DRAWDOWN_DEFENSE:**
1. ADX transition zone (20-25) = no new entries. Prevents trading in
   the most dangerous regime: the moment a trend is dying.
2. Each mode has its own stop: trend mode uses EMA crossover reversal;
   mean-reversion mode uses upper Bollinger Band breach.
3. max_trades_per_day=3 caps exposure during choppy regime cycling.
**VOLATILITY_DRAG_MITIGATION:** Bollinger Bands auto-scale to volatility.
ADX-based switching means the strategy always uses the appropriate
risk/reward framework for the current environment.
**ANTI_FRAGILITY_SCORE:** 9/10 — highest score in the cohort. The
transition zone dead-band is a genuine anti-fragility mechanism: the
strategy goes quiet exactly when market structure is most ambiguous.
**EXPECTED_SHARPE:** 1.05
**EXPECTED_SORTINO:** 1.35
**GRAVEYARD_AVOIDANCE:** ADX, EMA, Bollinger Bands — all computable from
OHLCV with no external dependencies. Regime switching is stateless and
deterministic — no hidden state accumulation across days.


## PHYSICS ENGINE CONSTRAINTS (HARD — non-negotiable)
- allow_fractional_shares=False (MES)
- max_contracts=1
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES 5m bars
- Inherit from: mantis_core/strategies/base.py BaseStrategy

## DELIVERABLE
A complete Python strategy file at:
mantis_core/strategies/lab/v_zoo_E1_003_regime_chameleon/v_zoo_E1_003_regime_chameleon.py

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
