# Mission: E5 Strategy — Momentum Breakout with Volume Confirmation

## Domain
00_PHYSICS_ENGINE

## Model Tier
Heavy (27b)

## Description
Generate a momentum breakout strategy that triggers on price breaking above
N-period highs with volume confirmation.

REQUIREMENTS:
- Detects when price exceeds highest high of last N periods
- Requires volume on breakout bar to exceed 1.5x average volume
- Entry: market buy on confirmed breakout
- Exit: trailing stop at 2x ATR below entry
- Must track win rate, average win, average loss, profit factor

OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/E5_003_momentum_breakout.py
ALLOWED IMPORTS: json, math, statistics, dataclasses, typing, pathlib, datetime
NO EXTERNAL LIBRARIES
TEST: Feed synthetic price series with clear breakout at bar 50. Assert BUY signal at bar 50. Assert trailing stop triggers on pullback. Assert trade log contains at least 1 complete round-trip.

## Acceptance Criteria
- highest_high(prices, period) returns float
- average_volume(volumes, period) returns float
- detect_breakout(price, high, volume, avg_vol, threshold=1.5) returns bool
- trailing_stop(entry_price, current_price, atr, multiplier=2.0) returns stop_price
- run_strategy(prices, volumes, period, atr_period) returns TradeLog
- TradeLog includes: trades list, win_rate, avg_win, avg_loss, profit_factor
