# Mission: 01_DATA_E3_002_multi_timeframe

## Domain
01_DATA_INGESTION

## Model Tier
Sprint (9b)

## Description
Build a multi-timeframe data aggregator that takes 5-minute candles
and produces 15-minute and 1-hour candles from them.

REQUIREMENTS:
1. Read 5m OHLCV CSV from a configurable path (default: data/crypto/BTCUSD_5m.csv)
2. Aggregate to 15m candles: group every 3 bars, use first open, max high, min low, last close, sum volume
3. Aggregate to 1h candles: group every 12 bars
4. Save to data/crypto/BTCUSD_15m.csv and data/crypto/BTCUSD_1h.csv
5. Handle partial periods at the end gracefully (drop incomplete)
6. CLI: python3 scripts/mantis/timeframe_aggregator.py --input data/crypto/BTCUSD_5m.csv
7. Print summary: input rows, 15m output rows, 1h output rows

ALLOWED IMPORTS: csv, pathlib, datetime, sys, math, argparse
NO EXTERNAL DEPENDENCIES.
OUTPUT: scripts/mantis/timeframe_aggregator.py
TEST: Feed 120 five-minute candles. Assert 40 fifteen-minute candles. Assert 10 one-hour candles.
