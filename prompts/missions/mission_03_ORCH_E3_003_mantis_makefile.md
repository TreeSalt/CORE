# Mission: 03_ORCH_E3_003_mantis_makefile

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Create a Makefile for the MANTIS repository.

REQUIREMENTS:
1. make feed SYMBOL=BTC/USD — run Alpaca data feed
2. make aggregate — run timeframe aggregator
3. make backtest STRATEGY=regime_trend — run backtest
4. make walkforward STRATEGY=regime_trend — run walk-forward validation
5. make paper — start paper trading mode
6. make status — show positions and P&L
7. make install — pip install requirements and core-sdk
8. make test — run MANTIS tests
9. make help — show all commands with descriptions

OUTPUT: mantis_config/Makefile
TEST: Assert contains make feed and make backtest
