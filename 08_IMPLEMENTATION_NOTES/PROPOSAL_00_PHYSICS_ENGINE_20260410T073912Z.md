---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

tests/smoke/test_mantis_v2_smoke.py

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from io import StringIO

from mantis.core.data_provider import CsvDataProvider
from mantis.core.signal_generator import SignalGenerator
from mantis.core.position_sizer import PositionSizer
from mantis.core.circuit_breaker import CircuitBreaker
from mantis.dashboard.state_manager import StateManager


class TestMantisV2Smoke:
    """End-to-end smoke tests for v2 pipeline."""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic test data for the pipeline."""
        rows = []
        for i in range(100):
            row = {
                'timestamp': f'2024-01-0{i:02d} 12:00:00',
                'symbol': 'AAPL',
                'price': 150 + (i % 20),
                'volume': 10000 + i * 100,
                'indicator_sma': 148 + (i % 10),
                'indicator_rsi': 50 + (i % 30)
            }
            rows.append(row)
        return pd.DataFrame(rows)
    
    @pytest.fixture
    def data_provider(self, synthetic_data):
        """Setup CsvDataProvider with synthetic data."""
        csv_buffer = StringIO(synthetic_data.to_csv(index=False))
        provider = CsvDataProvider(csv_buffer)
        return provider
    
    def test_pipeline_produces_signals(self, data_provider):
        """Verify pipeline produces signals from input data."""
        signal_gen = SignalGenerator()
        signals = signal_gen.generate(data_provider)
        
        assert len(signals) > 0
        assert hasattr(signals, 'to_df') or isinstance(signals, pd.DataFrame)
    
    def test_position_sizing_triggers(self, synthetic_data):
        """Verify position sizing calculation works correctly."""
        sizer = PositionSizer()
        positions = sizer.calculate(150, 100000)
        
        assert positions is not None
        assert hasattr(positions, 'size') or isinstance(positions, dict)
    
    def test_circuit_breaker_respects_limits(self):
        """Verify circuit breaker respects loss limits."""
        cb = CircuitBreaker(max_loss=10000, recovery_minutes=30)
        
        # Test normal operation
        assert not cb.is_tripped()
        
        # Simulate hitting limit
        cb.update(-5000)  # Loss event
        assert not cb.is_tripped()
        
        cb.update(-6000)  # Total 11000 loss
        assert cb.is_tripped()
    
    def test_dashboard_state_writer(self, tmp_path):
        """Verify dashboard state is written correctly."""
        state = StateManager({})
        state.add_signal('buy', timestamp='2024-01-01 12:00:00')
        
        # Verify state can be accessed
        assert len(state.signals) > 0
        
        # Write to file
        output_path = tmp_path / 'dashboard_state.json'
        state.write(output_path)
        
        assert output_path.exists()
    
    def test_full_pipeline_end_to_end(self, synthetic_data):
        """End-to-end test of complete pipeline."""
        csv_buffer = StringIO(synthetic_data.to_csv(index=False))
        provider = CsvDataProvider(csv_buffer)
        
        signal_gen = SignalGenerator()
        signals = signal_gen.generate(provider)
        
        sizer = PositionSizer()
        positions = sizer.calculate(signals['price'].iloc[0], 100000)
        
        cb = CircuitBreaker(max_loss=50000)
        assert not cb.is_tripped()
        
        state = StateManager({})
        state.add_signal('buy', timestamp='2024-01-01 12:00:00')
        
        assert len(signals) > 0
        assert positions is not None
        assert not cb.is_tripped()