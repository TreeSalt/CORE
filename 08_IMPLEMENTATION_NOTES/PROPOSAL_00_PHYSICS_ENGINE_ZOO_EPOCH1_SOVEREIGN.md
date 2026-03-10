---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: SOVEREIGN — Alec W. Sanchez + Claude (Supreme Council)
TIER: sovereign
TYPE: STRATEGIC_ARCHITECTURE
STATUS: RATIFIED
DECISION: DECISION-SOVEREIGN-004
DATE: 2026-03-10
---

# Zoo Epoch 1 — Strategy Variant Blueprints
## Supreme Council Sovereign Edition

**Mandate:** Breed unkillable macro-survivors. Primary selection pressure:
`max_drawdown_pct < 15.0`. Secondary: `sortino_ratio > 1.0`.
Do NOT optimize for absolute return at expense of drawdown.

**PhysicsEngine Constraints (hard):**
- allow_fractional_shares=False (MES)
- max_contracts=1 (paper phase)
- no_overnight=True
- max_trades_per_day=3
- Instrument: MES (Micro E-mini S&P 500)
- Timeframe: 5m bars (system standard)

**Incumbent Champion:** TEST_1d — profit_factor 2.0, STAGING

---

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

---

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

---

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

---

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

---

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

---

## SELECTION_CRITERIA — Zoo Epoch 1 Ranking Protocol

Primary gate (eliminates disqualified variants):
- max_drawdown_pct MUST be < 15.0 over full backtest window
- Any variant exceeding 15% drawdown is ELIMINATED regardless of returns

Ranking (among surviving variants):
1. sortino_ratio — weighted 40% (downside risk-adjusted return)
2. sharpe_ratio — weighted 30% (total risk-adjusted return)
3. profit_factor — weighted 20% (gross profit / gross loss)
4. max_drawdown_pct — weighted 10% (lower is better, after gate)

Diversity bonus: If top 2 ranked variants share the same REGIME_AFFINITY,
the lower-ranked one is replaced by the highest-ranked variant with a
DIFFERENT regime affinity. The Zoo must field regime-diverse survivors.

Champion advancement: The highest-scoring variant that beats incumbent
TEST_1d on sortino_ratio advances to STAGING for Predatory Gate testing.

**SOVEREIGN NOTE:** ZOO_E1_003 (REGIME_CHAMELEON) is the theoretical
frontrunner on anti-fragility. ZOO_E1_001 (VOLATILITY_GATEKEEPER) is the
most conservative. Both should be evaluated carefully against the 15%
drawdown primary gate before ranking. The Zoo will decide.
