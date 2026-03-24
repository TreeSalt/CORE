"""Tests for crypto websocket feed stub."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.crypto_ws_feed")
    assert hasattr(mod, "CryptoWebSocketFeed")

def test_feed_creates():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_ws_feed")
    feed = mod.CryptoWebSocketFeed()
    assert feed is not None

def test_poll_returns_none_when_disconnected():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_ws_feed")
    feed = mod.CryptoWebSocketFeed()
    assert feed.poll() is None

def test_poll_returns_data_when_connected():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.crypto_ws_feed")
    feed = mod.CryptoWebSocketFeed()
    feed.connect({})
    feed.subscribe(["BTC_USDT"])
    msg = feed.poll()
    assert msg is not None
    assert "type" in msg
