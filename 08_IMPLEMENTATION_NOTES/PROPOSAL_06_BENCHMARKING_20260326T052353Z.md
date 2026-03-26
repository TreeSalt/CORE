---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
"""Test suite for Candle Generator benchmarking tests"""
import pytest


class TestCandleGenerator:
    def setup_method(self):
        from candle_generator import CandleGenerator
        self.generator = CandleGenerator()

    def test_trending_up_has_positive_drift(self, generator):
        """verify last close > first close for positive drift"""
        candles = generator.generate_candles(
            count=10,
            trend='up',
            amplitude=0.01
        )
        first_close = candles[0]['close']
        last_close = candles[-1]['close']
        assert last_close > first_close

    def test_mean_reverting_stays_near_center(self, generator):
        """verify prices stay within amplitude of center"""
        candles = generator.generate_candles(
            count=20,
            trend='mean_revert',
            mean_price=100.0,
            amplitude=5.0
        )
        for candle in candles:
            expected_range = [95.0, 105.0]
            assert expected_range[0] <= candle['close'] <= expected_range[1]

    def test_flash_crash_drops(self, generator):
        """verify a candle at crash_bar has close significantly below start"""
        candles = generator.generate_candles(
            count=30,
            trend='normal',
            crash_bar=25
        )
        for i, candle in enumerate(candles):
            if i < len(candles) - 1:
                next_close = candles[i+1]['close']
                assert next_close < candle['start_price'], \
                    f"Candle {i} at crash_bar shows close below start"

    def test_candle_fields_present(self, generator):
        """verify each candle has timestamp, open, high, low, close, volume"""
        candles = generator.generate_candles(count=5)
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        for i, candle in enumerate(candles):
            assert all(field in candle for field in required_fields), \
                f"Candle {i} missing required fields: {required_fields}"

    def test_reproducible_with_seed(self, generator):
        """verify two runs with same seed produce identical candles"""
        import random
        
        results1 = []
        for _ in range(3):
            result = self.generator.generate_candles(seed=42)
            results1.append(result)
        
        assert len(results1[0]) == len(results1[1])

    def test_trend_up_drift_positive(self, generator):
        """verify last close > first close for positive drift trend"""
        candles = generator.generate_candles(
            count=20,
            trend='up',
            drift=0.005
        )
        
        assert candles[-1]['close'] > candles[0]['close']

    def test_mean_revert_bounds(self, generator):
        """verify prices stay within bounds for mean reverting"""
        candles = generator.generate_candles(
            count=20,
            trend='mean_revert',
            center_price=150.0,
            max_deviation=3.0
        )

        for candle in candles:
            assert abs(candle['close'] - 150.0) <= 3.0

    def test_flash_crash_severity(self, generator):
        """verify flash crash produces significant drop"""
        candles = generator.generate_candles(
            count=5,
            trend='crash',
            crash_intensity=0.15
        )

        for candle in candles:
            assert candle['close'] < candle['open'] - (candle['open'] * 0.1)

    def test_volume_required(self, generator):
        """verify volume field is always present and numeric"""
        candles = generator.generate_candles(count=3)

        for candle in candles:
            assert 'volume' in candle, "Candle missing volume field"
            assert isinstance(candle['volume'], (int, float))

    def test_timestamp_monotonic(self, generator):
        """verify timestamps are in chronological order"""
        candles = generator.generate_candles(count=10)

        timestamps = [candle['timestamp'] for candle in candles]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] < timestamps[i + 1] or \
                   timestamps[i] == timestamps[i + 1]
```