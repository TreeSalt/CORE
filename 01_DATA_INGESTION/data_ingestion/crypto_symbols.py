"""Crypto symbol registry — pair metadata and order validation."""
from dataclasses import dataclass


@dataclass
class CryptoSymbol:
    base: str
    quote: str
    exchange: str
    min_lot: float
    tick_size: float
    fees_bps: int


SYMBOLS = {
    "BTC_USDT": CryptoSymbol("BTC", "USDT", "generic", 0.00001, 0.01, 10),
    "ETH_USDT": CryptoSymbol("ETH", "USDT", "generic", 0.0001, 0.01, 10),
    "SOL_USDT": CryptoSymbol("SOL", "USDT", "generic", 0.01, 0.01, 10),
    "AVAX_USDT": CryptoSymbol("AVAX", "USDT", "generic", 0.01, 0.01, 12),
    "LINK_USDT": CryptoSymbol("LINK", "USDT", "generic", 0.01, 0.001, 10),
    "DOT_USDT": CryptoSymbol("DOT", "USDT", "generic", 0.1, 0.001, 12),
    "MATIC_USDT": CryptoSymbol("MATIC", "USDT", "generic", 1.0, 0.0001, 10),
    "ADA_USDT": CryptoSymbol("ADA", "USDT", "generic", 1.0, 0.0001, 10),
    "DOGE_USDT": CryptoSymbol("DOGE", "USDT", "generic", 1.0, 0.00001, 15),
    "XRP_USDT": CryptoSymbol("XRP", "USDT", "generic", 1.0, 0.0001, 10),
}


def get_symbol(pair_str: str):
    return SYMBOLS.get(pair_str)


def list_symbols(exchange: str = "generic") -> list:
    return [s for s in SYMBOLS.values() if s.exchange == exchange]


def validate_order(symbol: CryptoSymbol, qty: float, price: float) -> bool:
    if qty < symbol.min_lot:
        return False
    if price % symbol.tick_size > symbol.tick_size * 0.01:
        return False
    return True
