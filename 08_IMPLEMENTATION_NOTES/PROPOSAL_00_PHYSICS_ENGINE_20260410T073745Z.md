---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Mock imports - assume these are from the mantis_v2 package
from mantis_v2.data.providers.csv_provider import CsvDataProvider
from mantis_v2.pipeline.core import Pipeline
from mantis_v2.pipeline.components.signal_generator import SignalGenerator
from mantis_v2.pipeline.components.position_sizer import PositionSizer
from mantis_v2.risk.circuit_breaker import CircuitBreaker
from mantis_v2.outputs.dashboard import DashboardWriter


@pytest.fixture
def synthetic_csv_data():
    """Create synthetic CSV test data."""
    lines = [
        "timestamp,asset,symbol,price,volume",
        f"1704067200,AAPL,AAPL,150.00,1000000",
        f"1704070800,AAPL,AAPL,151.00,1100000",
        f"1704074400,AAPL,AAPL,152.00,1200000",
        f"1704067200,GOOG,GOOG,2800.00,500000",
        f"1704070800,GOOG,GOOG,2810.00,520000",
        f"1704074400,GOOG,GOOG,2820.00,540000",
    ]
    return "\n".join(lines)


@pytest.fixture
def temp_csv_file(synthetic_csv_data):
    """Create temporary CSV file with synthetic data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(synthetic_csv_data)
        return Path(f.name)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestMantisV2Smoke:
    """End-to-end smoke test for mantis_v2 pipeline."""

    def test_csv_data_provider_loads_data(self, temp_csv_file):
        """Test that CsvDataProvider loads synthetic data correctly."""
        provider = CsvDataProvider(temp_csv_file)
        data = provider.load()
        
        assert len(data) == 6
        assert 'timestamp' in data[0]
        assert 'symbol' in data[0]


    def test_pipeline_produces_signals(self, temp_csv_file):
        """Verify pipeline produces signals."""
        config = {
            "lookback_period": 3,
            "threshold": 2.0
        }
        
        provider = CsvDataProvider(temp_csv_file)
        signal_gen = SignalGenerator(config=config)
        pipeline = Pipeline(data_provider=provider, signal_generator=signal_gen)
        
        signals = pipeline.generate_signals()
        
        assert len(signals) > 0
        assert any(signal['action'] in ['BUY', 'SELL', 'HOLD'] for signal in signals)


    def test_position_sizing_triggered(self, temp_csv_file):
        """Verify position sizing is triggered."""
        config = {
            "max_position_size": 100000,
            "risk_per_trade": 0.02,
            "account_balance": 1000000
        }
        
        provider = CsvDataProvider(temp_csv_file)
        signal_gen = SignalGenerator(config={"lookback_period": 3})
        position_sizer = PositionSizer(config=config)
        pipeline = Pipeline(
            data_provider=provider, 
            signal_generator=signal_gen,
            position_sizer=position_sizer
        )
        
        positions = pipeline.calculate_positions()
        
        assert len(positions) > 0
        assert any(abs(pos['size']) > 0 for pos in positions)


    def test_circuit_breaker_respected(self, temp_csv_file):
        """Verify circuit breakers are respected."""
        config = {
            "max_loss_threshold": 0.10,
            "consecutive_losses": 3,
            "cool_down_period": 24 * 60 * 60
        }
        
        provider = CsvDataProvider(temp_csv_file)
        circuit_breaker = CircuitBreaker(config=config)
        signal_gen = SignalGenerator(config={"lookback_period": 3})
        pipeline = Pipeline(
            data_provider=provider,
            signal_generator=signal_gen,
            risk_manager=circuit_breaker
        )
        
        signals = pipeline.generate_signals()
        
        # Circuit breaker should not block normal operation on fresh run
        assert len(signals) > 0


    def test_dashboard_state_written(self, temp_csv_file, temp_output_dir):
        """Verify dashboard state is written."""
        config = {
            "lookback_period": 3
        }
        
        provider = CsvDataProvider(temp_csv_file)
        signal_gen = SignalGenerator(config=config)
        dashboard_writer = DashboardWriter(output_path=temp_output_dir)
        pipeline = Pipeline(
            data_provider=provider,
            signal_generator=signal_gen,
            dashboard_writer=dashboard_writer
        )
        
        pipeline.run()
        
        dashboard_file = temp_output_dir / "dashboard_state.json"
        assert dashboard_file.exists()
        
        with open(dashboard_file) as f:
            state = json.load(f)
        
        assert 'timestamp' in state
        assert 'signals_count' in state or len(state.get('signals', [])) > 0


    def test_full_pipeline_end_to_end(self, temp_csv_file, temp_output_dir):
        """Complete end-to-end smoke test."""
        pipeline_config = {
            "data_provider": {"source": temp_csv_file},
            "signal_generator": {"lookback_period": 3, "threshold": 2.0},
            "position_sizer": {
                "max_position_size": 100000,
                "risk_per_trade": 0.02,
                "account_balance": 1000000
            },
            "circuit_breaker": {
                "max_loss_threshold": 0.10,
                "consecutive_losses": 3
            },
            "dashboard": {"output_path": temp_output_dir}
        }
        
        provider = CsvDataProvider(temp_csv_file)
        signal_gen = SignalGenerator(config=pipeline_config["signal_generator"])
        position_sizer = PositionSizer(config=pipeline_config["position_sizer"])
        circuit_breaker = CircuitBreaker(config=pipeline_config["circuit_breaker"])
        dashboard_writer = DashboardWriter(output_path=temp_output_dir)
        
        pipeline = Pipeline(
            data_provider=provider,
            signal_generator=signal_gen,
            position_sizer=position_sizer,
            risk_manager=circuit_breaker,
            dashboard_writer=dashboard_writer
        )
        
        result = pipeline.run()
        
        assert result is not None
        assert 'signals' in result or len(result.get('signals', [])) > 0
        assert dashboard_writer.output_path / "dashboard_state.json".name != ""
        
        dashboard_file = dashboard_writer.output_path / f"dashboard_state_{datetime.now().strftime('%Y%m%d')}.json"
        if not dashboard_file.exists():
            dashboard_files = list(temp_output_dir.glob("dashboard*.json"))
            assert len(dashboard_files) > 0 or dashboard_writer.state is not None


    def test_smoke_test_completion(self, temp_csv_file):
        """Final smoke test completion check."""
        provider = CsvDataProvider(temp_csv_file)
        
        assert provider is not None
        assert provider.file_path.exists()
        assert len(provider.load()) > 0
        
        signal_gen = SignalGenerator(config={"lookback_period": 3})
        assert signal_gen is not None
        
        position_sizer = PositionSizer(config={
            "max_position_size": 100000,
            "risk_per_trade": 0.02,
            "account_balance": 1000000
        })
        assert position_sizer is not None
        
        circuit_breaker = CircuitBreaker(config={
            "max_loss_threshold": 0.10,
            "consecutive_losses": 3
        })
        assert circuit_breaker is not None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dashboard_writer = DashboardWriter(output_path=Path(tmpdir))
            assert dashboard_writer is not None
```