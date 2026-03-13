# MISSION: Market Data Normalizer
DOMAIN: 01_DATA_INGESTION
TASK: implement_data_normalizer
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
1. Accept raw data from any feed adapter
2. Validate required columns (timestamp, OHLC, volume)
3. Timezone normalization (everything to UTC)
4. Detect anomalies: zero volume, negative prices, out-of-sequence timestamps
5. Compute derived fields: returns, log_returns, bar_duration
6. Output clean pd.DataFrame

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/data_normalizer.py

## CONSTRAINTS
- No external API calls
- Fail closed on negative prices
- Output valid Python only
