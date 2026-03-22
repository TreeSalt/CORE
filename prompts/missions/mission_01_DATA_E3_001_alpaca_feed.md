# Mission: 01_DATA_E3_001_alpaca_feed

## Domain
01_DATA_INGESTION

## Model Tier
Sprint (9b)

## Description
Build a cryptocurrency and stock price data collector using the Alpaca Markets paper trading REST endpoint.

AUTHENTICATION:
Read credentials from environment variables using os.environ.
The two variable names follow the pattern ALPACA_ prefix with standard suffixes.
Do NOT hardcode any values. Do NOT accept credentials as CLI arguments.
Refer to Alpaca docs for the correct header names.

CRYPTO DATA:
  GET https://data.alpaca.markets/v1beta3/crypto/us/bars
  Params: symbols=BTC/USD, timeframe=5Min, start=ISO8601 date, limit=1000
  Auth headers must be included per Alpaca documentation.

STOCK DATA:
  GET https://data.alpaca.markets/v2/stocks/bars
  Params: symbols=SPY, timeframe=5Min, start=ISO8601 date, limit=1000

REQUIREMENTS:
1. fetch_crypto_bars(symbol, timeframe, start_date) returns list of OHLCV dicts
2. fetch_stock_bars(symbol, timeframe, start_date) returns list of OHLCV dicts
3. save_to_csv(bars, filepath) saves with columns: timestamp,open,high,low,close,volume
4. Append mode: if file exists, only add bars newer than last timestamp
5. CLI: python3 scripts/mantis/alpaca_feed.py --symbol BTC/USD --timeframe 5Min --days 30
6. Handle rate limits gracefully (200 requests per minute)
7. Print summary: bars fetched, date range, file path

ALLOWED IMPORTS: os, urllib.request, json, csv, pathlib, datetime, time, sys, argparse
NO EXTERNAL DEPENDENCIES.
OUTPUT: scripts/mantis/alpaca_feed.py
TEST: Assert CSV is created with correct columns. Assert at least 50 rows returned.
