# Mission: 00_PHYSICS_E6_001_regime_trend

## Domain
00_PHYSICS_ENGINE

## Model Tier
Sprint (9b)

## Description
Build a volatility regime filter combined with trend following strategy
for BTC/USD. This is the first real MANTIS strategy for paper trading.

The strategy uses three rules:
- In LOW volatility regime: do nothing (preserve capital)
- In NORMAL volatility: follow the 20-period EMA trend with tight stops
- In HIGH volatility: reduce position size by 75 percent
- In CRISIS volatility: position size is zero

REQUIREMENTS:
1. calculate_ema(prices, period) — exponential moving average using multiplier 2/(period+1)
2. calculate_atr(highs, lows, closes, period) — average true range
3. classify_regime(atr_value, atr_history) — returns LOW, NORMAL, HIGH, CRISIS
   based on where current ATR sits relative to its own 50-period distribution
   below 25th percentile = LOW, 25-75 = NORMAL, 75-95 = HIGH, above 95 = CRISIS
4. generate_signals(ohlcv_rows) — returns list of Signal objects with action BUY SELL or HOLD
   BUY when close crosses above EMA in NORMAL regime
   SELL when close crosses below EMA or regime shifts to HIGH or CRISIS
5. calculate_position_size(regime, base_size, account_balance) — float scaled by regime
   NORMAL=base_size, HIGH=base_size*0.25, LOW=0, CRISIS=0
6. run_backtest(ohlcv_rows, initial_balance) — returns BacktestResult dataclass with:
   total_return, max_drawdown, win_rate, profit_factor, trade_count, sharpe_proxy

ALLOWED IMPORTS: math, statistics, csv, pathlib, dataclasses, typing, datetime
NO EXTERNAL DEPENDENCIES. No numpy. No pandas.
OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/E6_001_regime_trend_btc.py
TEST: Feed 500 rows with a clear uptrend. Assert at least 3 trades generated. Assert max_drawdown less than 20 percent.
