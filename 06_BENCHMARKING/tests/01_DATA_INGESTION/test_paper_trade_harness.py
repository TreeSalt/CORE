"""Tests for paper trade harness."""
import pytest

def test_required_imports_exist():
    import importlib
    mod = importlib.import_module("01_DATA_INGESTION.data_ingestion.paper_trade_harness")
    assert hasattr(mod, "PaperTradeHarness")

def test_submit_order_returns_fill():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.paper_trade_harness")
    h = mod.PaperTradeHarness(initial_cash=100000)
    result = h.submit_order("BTC_USDT", "buy", 1.0, 50000.0)
    assert result["status"] == "FILLED"
    assert "order_id" in result
    assert result["fill_price"] > 50000.0

def test_get_position_after_fill():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.paper_trade_harness")
    h = mod.PaperTradeHarness(initial_cash=100000)
    h.submit_order("BTC_USDT", "buy", 1.0, 50000.0)
    pos = h.get_position("BTC_USDT")
    assert pos["qty"] == 1.0
    assert pos["avg_price"] > 0

def test_slippage_applied():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.paper_trade_harness")
    h = mod.PaperTradeHarness(initial_cash=100000, default_slippage_pct=0.1)
    result = h.submit_order("BTC_USDT", "buy", 1.0, 50000.0)
    assert result["fill_price"] != 50000.0

def test_portfolio_equity():
    from importlib import import_module
    mod = import_module("01_DATA_INGESTION.data_ingestion.paper_trade_harness")
    h = mod.PaperTradeHarness(initial_cash=100000)
    h.submit_order("BTC_USDT", "buy", 1.0, 50000.0)
    portfolio = h.get_portfolio(prices={"BTC_USDT": 55000.0})
    assert portfolio["total_equity"] > 0
    assert portfolio["total_equity"] == portfolio["cash"] + portfolio["positions"]["BTC_USDT"]["market_value"]
