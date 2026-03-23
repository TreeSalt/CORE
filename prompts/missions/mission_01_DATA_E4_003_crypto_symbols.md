# MISSION: Crypto Symbol Registry
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_symbols.py

## REQUIREMENTS
- Define CryptoSymbol dataclass: base, quote, exchange, min_lot, tick_size, fees_bps
- Pre-populate 10 major pairs: BTC/USDT, ETH/USDT, SOL/USDT, etc.
- get_symbol(pair_str) -> CryptoSymbol
- list_symbols(exchange=None) -> list
- validate_order(symbol, qty, price) -> bool (checks lot size, tick)
- No external API calls
- Output valid Python only
