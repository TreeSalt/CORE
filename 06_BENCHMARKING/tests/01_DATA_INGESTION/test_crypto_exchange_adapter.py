"""Tests for crypto exchange adapter."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.crypto_exchange_adapter")
    assert hasattr(mod, "CryptoExchangeAdapter")

def test_adapter_creates():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_exchange_adapter")
    adapter = mod.CryptoExchangeAdapter()
    assert adapter is not None

def test_fetch_returns_list():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_exchange_adapter")
    adapter = mod.CryptoExchangeAdapter()
    candles = adapter.fetch_ohlcv("BTC_USDT", "1m", limit=5)
    assert isinstance(candles, list)
    assert len(candles) == 5

def test_candle_has_required_fields():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_exchange_adapter")
    adapter = mod.CryptoExchangeAdapter()
    candles = adapter.fetch_ohlcv("BTC_USDT", "1m", limit=1)
    c = candles[0]
    for field in ["timestamp", "open", "high", "low", "close", "volume"]:
        assert field in c, f"Missing field: {field}"
