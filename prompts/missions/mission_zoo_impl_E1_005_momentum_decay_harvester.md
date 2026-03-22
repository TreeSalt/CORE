# MISSION: Implement Zoo Variant ZOO_E1_005 — MOMENTUM_DECAY_HARVESTER
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_zoo_variant
VARIANT: ZOO_E1_005
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Implement the MOMENTUM_DECAY_HARVESTER strategy as a certified strategy class conforming to
the mantis_core strategy base contract.

## BLUEPRINT
## ZOO_E1_005 — MOMENTUM_DECAY_HARVESTER

**STRATEGY_ID:** ZOO_E1_005
**CORE_LOGIC:** Captures the predictable decay pattern of intraday momentum
moves. Enter long when: (1) price has moved up >0.3% in a single 5m bar
(momentum spike), AND (2) the following bar opens inside the spike bar's
range (consolidation signal). This is a pullback entry — we are not chasing
the spike, we are buying the first pause after it. Target: 0.5x the original
spike size. Stop: below the low of the consolidation bar.
**TIMEFRAME:** 5m
**REGIME_AFFINITY:** Any regime with intraday momentum spikes — works in
both trending and volatile environments because it harvests the aftermath
of moves, not the moves themselves.
**DRAWDOWN_DEFENSE:**
1. Requires consolidation bar (pullback entry) — never buys the top of
   a spike. This single rule eliminates the majority of momentum-chasing
   drawdown.
2. Stop below consolidation bar low — tight, structure-based stop.
3. Fixed reward:risk of approximately 1.5:1 (0.5x spike target vs
   consolidation bar range stop).
4. max_trades_per_day=3 caps total daily exposure.
**VOLATILITY_DRAG_MITIGATION:** The consolidation requirement naturally
filters for lower-volatility entry points WITHIN volatile sessions.
Entering during consolidation means entering when short-term vol is
compressing — optimal risk/reward timing.
**ANTI_FRAGILITY_SCORE:** 8/10 — the pullback entry mechanic means the
strategy benefits from volatility (more spikes = more opportunities) while
the consolidation filter protects against the worst of it. Genuinely
asymmetric exposure.
**EXPECTED_SHARPE:** 0.92
**EXPECTED_SORTINO:** 1.25
**GRAVEYARD_AVOIDANCE:** All logic is pure price arithmetic — percentage
moves, bar high/low comparisons. No indicators with external library
dependencies. No state carried across sessions. Stateless and auditable.


## PHYSICS ENGINE CONSTRAINTS (HARD — non-negotiable)
- allow_fractional_shares=False (MES)
- max_contracts=1
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES 5m bars
- Inherit from: mantis_core/strategies/base.py BaseStrategy

## DELIVERABLE
A complete Python strategy file at:
mantis_core/strategies/lab/v_zoo_E1_005_momentum_decay_harvester/v_zoo_E1_005_momentum_decay_harvester.py

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
