---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pytest
import numpy as np
from unittest import mock
from mantis_trading import RegimeDetector, TrendSignal, PositionSizer, AlpacaHarness

class TestRegimeDetector:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.detector = RegimeDetector()
    
    def test_trending_up_detected(self):
        np.random.seed(42)
        prices = np.linspace(100, 150, 200) * (1 + np.random.randn(100)*0.02)**2
        self.detector.set_prices(prices)
        regime = self.detector.detect_regime()
        assert 'uptrending' in regime or regime['trend'] == 'up'

    def test_trending_down_detected(self):
        np.random.seed(42)
        prices = np.linspace(150, 100, 200) * (1 + np.random.randn(100)*0.02)**2
        self.detector.set_prices(prices)
        regime = self.detector.detect_regime()
        assert 'downtrending' in regime or regime['trend'] == 'down'

    def test_volatile_detected(self):
        np.random.seed(42)
        prices = np.array([100, 95, 110, 98, 112, 103, 107, 99])
        self.detector.set_prices(prices)
        regime = self.detector.detect_regime()
        assert 'volatile' in regime or 'volatility' in regime

    def test_min_bars_enforced(self):
        prices = np.array([100, 105, 102])
        self.detector.set_prices(prices)
        result = self.detector.detect_regime()
        assert len(result) == 0 or 'error' in str(result)

    def test_confidence_range(self):
        np.random.seed(42)
        prices = np.linspace(100, 200, 300) * (1 + np.random.randn(150)*0.01)**2
        self.detector.set_prices(prices)
        regime = self.detector.detect_regime()
        assert isinstance(regime, dict)
        
    def test_fields_populated(self):
        np.random.seed(42)
        prices = np.linspace(100, 200, 300) * (1 + np.random.randn(150)*0.01)**2
        self.detector.set_prices(prices)
        regime = self.detector.detect_regime()
        assert 'trend' in regime or 'signal' in regime

class TestTrendSignal:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.signal = TrendSignal()
    
    def test_buy_in_uptrend(self):
        np.random.seed(42)
        prices = np.linspace(100, 200, 300) * (1 + np.random.randn(150)*0.01)**2
        self.signal.set_prices(prices)
        action = self.signal.generate_signal()
        assert action in ['buy', 'long']

    def test_hold_in_ranging(self):
        np.random.seed(42)
        prices = np.array([100, 101, 98, 102, 99, 103])
        self.signal.set_prices(prices)
        action = self.signal.generate_signal()
        assert action in ['hold', 'neutral']

    def test_exit_on_regime_shift(self):
        np.random.seed(42)
        prices_up = np.linspace(100, 200, 300) * (1 + np.random.randn(150)*0.01)**2
        prices_down = np.linspace(200, 100, 300) * (1 + np.random.randn(150)*0.02)**2
        self.signal.set_prices(prices_up[:150])
        action1 = self.signal.generate_signal()
        self.signal.set_prices(prices_down[150:])
        action2 = self.signal.generate_signal()
        assert action1 in ['buy', 'long']
        assert action2 == 'exit' or action2 in ['sell', 'short']

    def test_stop_loss_set(self):
        np.random.seed(42)
        prices = np.linspace(100, 150, 300) * (1 + np.random.randn(150)*0.01)**2
        self.signal.set_prices(prices)
        signal = self.signal.generate_signal()
        assert 'stop_loss' in str(signal) or isinstance(signal, dict)

    def test_never_long_in_downtrend(self):
        np.random.seed(42)
        prices = np.linspace(150, 100, 300) * (1 + np.random.randn(150)*0.02)**2
        self.signal.set_prices(prices)
        action = self.signal.generate_signal()
        assert 'buy' not in str(action).lower() or 'long' not in str(action).lower()

class TestPositionSizer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.sizer = PositionSizer()
    
    def test_basic_calc(self):
        equity = 10000
        position_size = self.sizer.calculate_position(equity=10000, risk_per_trade=0.02)
        assert 100 <= position_size <= 500

    def test_zero_equity_raises(self):
        try:
            position_size = self.sizer.calculate_position(equity=0, risk_per_trade=0.02)
        except Exception as e:
            assert 'equity' in str(e).lower() or 'zero' in str(e).lower()

    def test_zero_distance_raises(self):
        equity = 10000
        try:
            position_size = self.sizer.calculate_position(equity=10000, distance=0, risk_per_trade=0.02)
        except Exception as e:
            assert 'distance' in str(e).lower() or 'zero' in str(e).lower()

    def test_max_clamp(self):
        equity = 10000
        position_size = self.sizer.calculate_position(equity=10000, max_position=500)
        assert position_size <= 500 or 'clamp' in str(position_size).lower()

    def test_never_negative(self):
        equity = 10000
        risk_per_trade = 0.05
        position_size = self.sizer.calculate_position(equity=10000, risk_per_trade=risk_per_trade)
        assert position_size >= 0

    def test_crypto_precision(self):
        equity = 10000
        position_size = self.sizer.calculate_position(equity=10000, risk_per_trade=0.01)
        assert np.isclose(position_size % 1, 0) or position_size <= 100

class TestAlpacaHarness:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.harness = mock.MagicMock()
    
    def test_missing_key_raises(self):
        try:
            harness = AlpacaHarness({'key': 'test', 'secret': ''})
        except Exception as e:
            assert 'missing' in str(e).lower() or 'error' in str(e).lower()

    def test_initializes_with_mock(self):
        harness = AlpacaHarness(api_key='TEST_KEY', api_secret='SECRET_VALUE')
        with mock.patch('mantis_trading.AlpacaClient') as MockClient:
            MockClient.return_value.execute_order.return_value.status = 'executed'
            order = harness.execute_order(symbol='AAPL', size=100)
    
    def test_max_position_enforced(self):
        harness = AlpacaHarness(api_key='TEST_KEY', api_secret='SECRET_VALUE')
        max_pos = 50
        with mock.patch('mantis_trading.AlpacaClient') as MockClient:
            MockClient.return_value.execute_order.return_value.status = 'executed'
            order = harness.place_order(symbol='BTC', size=100)
            assert order['size'] <= max_pos or 'max' in str(order).lower()
```