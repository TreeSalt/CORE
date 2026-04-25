# MISSION: MANTIS Trend Signal Generator
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E11_002_trend_signal
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
With regime classification done, the signal generator produces BUY/SELL/HOLD
decisions. It only generates trend-following signals in TRENDING regimes.

## BLUEPRINT
1. TRENDING_UP: ENTER LONG on price cross above 20-EMA when 20-EMA > 50-EMA.
   EXIT when price below 20-EMA or regime shifts. Never SHORT.
2. TRENDING_DOWN: ENTER SHORT on price cross below 20-EMA when 20-EMA < 50-EMA.
   EXIT when price above 20-EMA or regime shifts. Never LONG.
3. RANGING/VOLATILE: flatten any position, otherwise HOLD.

Output TradeSignal with: signal enum, confidence, regime, entry_price,
stop_loss (1.5x ATR), take_profit (3x ATR), timestamp.

generate_signal(closes, highs, lows, current_regime, current_position) -> TradeSignal

## DELIVERABLE
File: mantis_core/physics/trend_signal.py

## CONSTRAINTS
- numpy only (no talib, no pandas)
- Import RegimeState and Regime from regime_detector
- Stop/TP from ATR
- Output valid Python only
