"""Tests for crypto symbol registry."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.crypto_symbols")
    assert hasattr(mod, "get_symbol")
    assert hasattr(mod, "list_symbols")
    assert hasattr(mod, "SYMBOLS")

def test_get_known_symbol():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_symbols")
    sym = mod.get_symbol("BTC_USDT")
    assert sym is not None
    assert sym.base == "BTC"

def test_get_unknown_symbol():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_symbols")
    assert mod.get_symbol("FAKE_PAIR") is None

def test_symbols_count():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_symbols")
    assert len(mod.SYMBOLS) == 10
