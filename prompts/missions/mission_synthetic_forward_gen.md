# MISSION: Synthetic Forward Data Generator
DOMAIN: 01_DATA_INGESTION
TASK: implement_synthetic_forward_generator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The paper trading harness needs forward-looking data to simulate real-time
trading. Until we connect to live IBKR feeds, we need a synthetic data
generator that produces realistic MES 5m OHLCV bars with configurable
regime characteristics (trending, mean-reverting, volatile, calm).

## BLUEPRINT
Create a SyntheticForwardGenerator that:
1. Generates N days of 5m OHLCV bars for MES
2. Configurable regimes: TREND_UP, TREND_DOWN, MEAN_REVERT, HIGH_VOL, LOW_VOL
3. Regime transitions happen at configurable intervals
4. Volume profile follows realistic intraday patterns (high at open/close)
5. Includes random gap opens between sessions
6. Seeded for reproducibility
7. Outputs pd.DataFrame in standard OHLCV format

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/synthetic_forward_generator.py

## CONSTRAINTS
- Deterministic (seeded RNG)
- No external API calls or data files
- Output valid Python only
