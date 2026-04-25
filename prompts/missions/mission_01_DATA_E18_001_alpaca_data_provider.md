# MISSION: mantis_data_provider_alpaca
TYPE: IMPLEMENTATION
MISSION_ID: 01_DATA_E18_001_alpaca_data_provider

## DELIVERABLE
File: mantis_core/data_providers/alpaca_provider.py

## INTERFACE CONTRACT
### Class: AlpacaDataProvider
Implements the AbstractDataProvider interface from MANTIS_DATA_PROVIDER.md.
Methods: get_bars, get_quote, subscribe_stream, close.
Reads ALPACA_API_KEY and ALPACA_SECRET_KEY from env.
