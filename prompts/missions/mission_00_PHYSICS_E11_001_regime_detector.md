# MISSION: MANTIS Regime Detector — BTC/USD Market State Classifier
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E11_001_regime_detector
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
MANTIS targets BTC/USD with a regime-aware trend-following strategy. Before any
signal generation, the system must classify the current market regime.

## BLUEPRINT
Classify BTC/USD into four states:

1. TRENDING_UP — ADX > 25, +DI > -DI, price above 50-EMA, ATR expanding
2. TRENDING_DOWN — ADX > 25, -DI > +DI, price below 50-EMA
3. RANGING — ADX < 20, Bollinger width contracting
4. VOLATILE — ATR > 2x 50-bar average OR single bar > 3x ATR

Interface: classify_regime(closes, highs, lows) -> RegimeState
RegimeState contains: regime (enum), confidence, adx, atr, atr_ratio, timestamp

All indicators computed from raw arrays with numpy. No talib.
ADX/DI from Wilder smoothing. EMA from standard exponential formula.

## DELIVERABLE
File: mantis_core/physics/regime_detector.py

## CONSTRAINTS
- numpy only (no talib, no pandas)
- All indicator math from scratch
- Minimum 100 bars required, raise ValueError if fewer
- Output valid Python only
