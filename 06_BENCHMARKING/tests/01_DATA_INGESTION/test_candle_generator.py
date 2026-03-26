"""Tests for candle generator — matches actual module API."""
import pytest
from importlib import import_module


@pytest.fixture
def gen():
    return import_module("01_DATA_INGESTION.data_ingestion.candle_generator")


def test_trending_up_has_positive_drift(gen):
    candles = gen.generate_trending(100, start_price=100.0, drift_pct=0.5, seed=42)
    assert candles[-1]["close"] > candles[0]["open"]


def test_mean_reverting_stays_near_center(gen):
    candles = gen.generate_mean_reverting(200, center_price=100.0, amplitude_pct=5.0, seed=42)
    closes = [c["close"] for c in candles]
    assert all(80 < c < 120 for c in closes), "Prices strayed too far from center"


def test_volatile_has_large_swings(gen):
    candles = gen.generate_volatile(100, start_price=100.0, volatility_pct=5.0, seed=42)
    returns = [abs(candles[i]["close"] - candles[i-1]["close"]) / candles[i-1]["close"]
               for i in range(1, len(candles))]
    assert max(returns) > 0.01, "Expected at least one 1%+ move"


def test_flash_crash_drops(gen):
    candles = gen.generate_flash_crash(100, start_price=100.0, crash_bar=50, crash_pct=30.0, seed=42)
    assert candles[50]["close"] < 80, "Flash crash should drop price significantly"


def test_candle_fields_present(gen):
    candles = gen.generate_trending(5, seed=42)
    for c in candles:
        for field in ["timestamp", "open", "high", "low", "close", "volume"]:
            assert field in c, f"Missing field: {field}"


def test_reproducible_with_seed(gen):
    a = gen.generate_trending(10, seed=99)
    b = gen.generate_trending(10, seed=99)
    assert a == b, "Same seed should produce identical candles"


def test_timestamp_monotonic(gen):
    candles = gen.generate_trending(50, seed=42)
    timestamps = [c["timestamp"] for c in candles]
    assert timestamps == sorted(timestamps), "Timestamps should be monotonically increasing"
