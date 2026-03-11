# MISSION: Implement Zoo Variant ZOO_E1_001 — VOLATILITY_GATEKEEPER
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E1_001
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Implement the VOLATILITY_GATEKEEPER strategy as a certified strategy class conforming to
the antigravity_harness strategy base contract.

## BLUEPRINT
## ZOO_E1_001 — VOLATILITY_GATEKEEPER

**STRATEGY_ID:** ZOO_E1_001
**CORE_LOGIC:** Volatility-adaptive trend filter with ATR-based entry gate.
Entry only permitted when 20-period ATR is below its own 50-period moving
average (i.e. volatility is contracting, not expanding). Within that regime,
enter long on EMA(9) crossing above EMA(21) on 5m bars. Exit on EMA(9)
crossing below EMA(21) OR when ATR expands above its 50-period MA (regime
invalidation). Hard stop: 2x ATR from entry.
**TIMEFRAME:** 5m
**REGIME_AFFINITY:** Low-volatility trending — enters calm before momentum,
exits before volatility expansion punishes position.
**DRAWDOWN_DEFENSE:**
1. ATR gate prevents entries during high-vol regimes (primary)
2. Hard stop at 2x ATR from entry (maximum loss per trade bounded)
3. max_trades_per_day=3 enforced — no revenge trading after 2 losses
4. no_overnight=True — gap risk eliminated entirely
**VOLATILITY_DRAG_MITIGATION:** Only trades when vol is contracting — avoids
the whipsaw chop that destroys momentum strategies in expanding vol regimes.
**ANTI_FRAGILITY_SCORE:** 8/10 — ATR gate acts as automatic Black Swan
circuit breaker. High-vol crisis events trigger ATR expansion, which closes
the entry gate before damage accumulates.
**EXPECTED_SHARPE:** 0.95
**EXPECTED_SORTINO:** 1.20
**GRAVEYARD_AVOIDANCE:** No SSL/websocket calls in strategy logic. No
hardcoded parameters — all thresholds derived dynamically from ATR. Avoids
the static parameter fragility that killed early Physics Engine iterations.


## PHYSICS ENGINE CONSTRAINTS (HARD — non-negotiable)
- allow_fractional_shares=False (MES)
- max_contracts=1
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES 5m bars
- Inherit from: antigravity_harness/strategies/base.py BaseStrategy

## DELIVERABLE
A complete Python strategy file at:
antigravity_harness/strategies/lab/v_zoo_E1_001_volatility_gatekeeper/v_zoo_E1_001_volatility_gatekeeper.py

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
