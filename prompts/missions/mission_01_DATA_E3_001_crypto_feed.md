# Mission: 01_DATA_E3_001_crypto_feed

## Domain
01_DATA_INGESTION

## Model Tier
Sprint (9b)

## Description
Build a cryptocurrency price data collector that fetches OHLCV candles
from a free public API and stores them locally.

REQUIREMENTS:
1. Fetch BTC/USDT candles from the Binance public API (no auth required)
   Endpoint: https://api.binance.com/api/v3/klines
   Params: symbol=BTCUSDT, interval=5m, limit=1000
2. Parse response into standardized OHLCV format: timestamp, open, high, low, close, volume
3. Save to CSV at data/crypto/BTCUSDT_5m.csv
4. Append mode — if file exists, only add candles newer than the last timestamp
5. Print summary: candles fetched, date range, file size
6. Handle network errors gracefully with retry (3 attempts, 5s backoff)

ALLOWED IMPORTS: urllib.request, json, csv, pathlib, datetime, time, sys
NO EXTERNAL DEPENDENCIES. No pandas. No ccxt. Pure stdlib.
OUTPUT: scripts/mantis/crypto_feed.py
TEST: Assert CSV is created. Assert it has columns: timestamp,open,high,low,close,volume. Assert at least 100 rows.
