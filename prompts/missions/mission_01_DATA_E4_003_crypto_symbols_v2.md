# MISSION: Crypto Symbol Registry
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 01_DATA_INGESTION/data_ingestion/crypto_symbols.py

## REQUIREMENTS
- CryptoSymbol dataclass: base (str), quote (str), exchange (str), min_lot (float), tick_size (float), fees_bps (int)
- SYMBOLS dict mapping string pair names to CryptoSymbol instances for 10 major pairs
- get_symbol(pair_str) -> CryptoSymbol or None
- list_symbols(exchange) -> list of CryptoSymbol
- validate_order(symbol, qty, price) -> bool: checks lot size and tick constraints
- No external calls of any kind
- Output valid Python only
