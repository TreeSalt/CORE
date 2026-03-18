# Mission: E5 Strategy — Z-Score Mean Reversion

## Domain
00_PHYSICS_ENGINE

## Model Tier
Heavy (27b)

## Description
Generate a mean reversion strategy based on z-score deviation from a rolling mean.

REQUIREMENTS:
- Computes rolling mean and standard deviation over configurable window
- Generates BUY signal when z-score < -2.0 (oversold)
- Generates SELL signal when z-score > +2.0 (overbought)
- HOLD otherwise
- Must include maximum position limit
- Must include stop-loss at z-score = -3.0 (further deviation = cut losses)
- Must track entry price and compute P&L for each round-trip trade

OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/E5_002_mean_reversion.py
ALLOWED IMPORTS: json, math, statistics, dataclasses, typing, pathlib, datetime
NO EXTERNAL LIBRARIES
TEST: Feed synthetic mean-reverting price series. Assert at least 2 BUY and 2 SELL signals. Assert stop-loss triggers when z-score exceeds -3.0. Assert P&L tracking produces non-empty trade log.

## Acceptance Criteria
- rolling_mean(prices, window) returns list of floats
- rolling_std(prices, window) returns list of floats
- compute_zscore(price, mean, std) returns float
- generate_signals(prices, window, entry_z, exit_z, stop_z) returns list of Signal objects
- Signal enum: BUY, SELL, HOLD, STOP_LOSS
- track_trades(signals, prices) returns TradeLog with round-trip P&L
- All imports from Python stdlib only
