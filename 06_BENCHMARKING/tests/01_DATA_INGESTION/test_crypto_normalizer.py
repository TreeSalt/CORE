"""Tests for crypto normalizer."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.crypto_normalizer")
    assert hasattr(mod, "validate_integrity")
    assert hasattr(mod, "normalize_timestamps")
    assert hasattr(mod, "fill_gaps")

def test_validate_integrity_clean():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_normalizer")
    candles = [
        {"timestamp": 1000, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        {"timestamp": 2000, "open": 1.5, "high": 2.5, "low": 1, "close": 2, "volume": 200},
    ]
    result = mod.validate_integrity(candles)
    assert result["valid"] is True

def test_validate_integrity_negative():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_normalizer")
    candles = [{"timestamp": 1000, "open": -1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100}]
    result = mod.validate_integrity(candles)
    assert result["valid"] is False
