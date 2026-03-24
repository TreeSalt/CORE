"""Tests for crypto backfill."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.crypto_backfill")
    assert hasattr(mod, "backfill")

def test_backfill_returns_list():
    from importlib import import_module
    adapter_mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_exchange_adapter")
    backfill_mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_backfill")
    adapter = adapter_mod.CryptoExchangeAdapter()
    result = backfill_mod.backfill(adapter, "BTC_USDT", "2024-01-01", "2024-01-02", "1h")
    assert isinstance(result, list)
    assert len(result) > 0
