"""
RESILIENCE TESTS
-----------------
Verifies mid-flight self-healing, error containment, and data integrity guards.
These tests ensure the harness never crashes from its own errors.
"""

import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from antigravity_harness.models import SimulationContext
from antigravity_harness.paths import _safe_mkdir

# ─── Phase 1: ensure_dirs() Auto-Heal ─────────────────────────────────────

class TestEnsureDirsHealing:
    """Verify ensure_dirs() self-heals file-blocking-dir attacks (V249/V265)."""

    def test_safe_mkdir_creates_dir(self, tmp_path):
        target = tmp_path / "new_dir"
        _safe_mkdir(target)
        assert target.is_dir()

    def test_safe_mkdir_heals_file_blocking(self, tmp_path):
        target = tmp_path / "reports"
        target.touch()  # Create a FILE where a DIR is expected
        assert target.is_file()

        _safe_mkdir(target)
        assert target.is_dir()  # Auto-healed: file -> directory

    def test_safe_mkdir_noop_on_existing_dir(self, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()
        marker = target / "marker.txt"
        marker.touch()

        _safe_mkdir(target)
        assert target.is_dir()
        assert marker.exists()  # Contents preserved


# ─── Phase 2: FlightRecorder ────────────────────────────────────────────

class TestFlightRecorder:
    """Verify FlightRecorder logs errors and recoveries correctly."""

    def test_record_error(self, tmp_path):
        from antigravity_harness.phoenix import FlightRecorder
        FlightRecorder._instance = None
        recorder = FlightRecorder.instance(log_dir=tmp_path)

        try:
            raise ValueError("test explosion")
        except ValueError as e:
            recorder.record_error("test_source", e, severity="CRITICAL")

        assert len(recorder._events) == 1
        assert recorder._events[0]["type"] == "ERROR"
        assert recorder._events[0]["error"] == "test explosion"
        assert recorder._events[0]["severity"] == "CRITICAL"
        FlightRecorder._instance = None

    def test_record_recovery(self, tmp_path):
        from antigravity_harness.phoenix import FlightRecorder
        FlightRecorder._instance = None
        recorder = FlightRecorder.instance(log_dir=tmp_path)

        recorder.record_recovery("test_source", "HEAL_DIR", "Replaced file with dir")

        assert len(recorder._events) == 1
        assert recorder._events[0]["type"] == "RECOVERY"
        assert recorder._events[0]["action"] == "HEAL_DIR"
        FlightRecorder._instance = None

    def test_flush_persists_to_disk(self, tmp_path):
        import json

        from antigravity_harness.phoenix import FlightRecorder
        FlightRecorder._instance = None
        recorder = FlightRecorder.instance(log_dir=tmp_path)

        try:
            raise RuntimeError("boom")
        except RuntimeError as e:
            recorder.record_error("flush_test", e)

        path = recorder.flush()
        assert path is not None
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["event_count"] == 1
        assert data["events"][0]["error"] == "boom"
        FlightRecorder._instance = None

    def test_flush_returns_none_when_empty(self, tmp_path):
        from antigravity_harness.phoenix import FlightRecorder
        FlightRecorder._instance = None
        recorder = FlightRecorder.instance(log_dir=tmp_path)
        assert recorder.flush() is None
        FlightRecorder._instance = None


# ─── Phase 3: Runner Resilience ────────────────────────────────────────────

class TestRunnerResilience:
    """Verify SovereignRunner returns FAIL results instead of crashing."""

    def test_runner_survives_gate_crash(self):
        from antigravity_harness.phoenix import FlightRecorder
        from antigravity_harness.runner import SovereignRunner
        FlightRecorder._instance = None

        runner = SovereignRunner()
        mock_ctx = MagicMock(spec=SimulationContext)
        mock_ctx.params = MagicMock()
        mock_ctx.params.model_dump.return_value = {}

        with patch("antigravity_harness.runner.evaluate_gates", side_effect=RuntimeError("GATE BOMB")):
            result = runner.run_simulation(mock_ctx)

        assert result.status == "FAIL"
        assert "RUNTIME_ERROR" in result.fail_reason
        assert "GATE BOMB" in result.fail_reason
        FlightRecorder._instance = None

    def test_runner_survives_metric_extraction_crash(self):
        from antigravity_harness.phoenix import FlightRecorder
        from antigravity_harness.runner import SovereignRunner
        FlightRecorder._instance = None

        runner = SovereignRunner()
        mock_ctx = MagicMock(spec=SimulationContext)
        mock_ctx.params = MagicMock()
        mock_ctx.params.model_dump.return_value = {}

        with patch("antigravity_harness.runner.evaluate_gates", return_value="not_a_list"), \
             patch("antigravity_harness.runner._status_from_gate_results", side_effect=TypeError("bad type")):
            result = runner.run_simulation(mock_ctx)

        assert result.status == "FAIL"
        assert "RUNTIME_ERROR" in result.fail_reason
        FlightRecorder._instance = None


# ─── Phase 4: Data Integrity Guard ──────────────────────────────────────

class TestDataIntegrityGuard:
    """Verify NaN and zero-volume detection in _run_sim."""

    def test_nan_in_ohlc_detected(self):
        from antigravity_harness.gates import _run_sim

        df = pd.DataFrame({
            "Open": [100.0, 101.0, float("nan")],
            "High": [105.0, 106.0, 107.0],
            "Low": [95.0, 96.0, 97.0],
            "Close": [102.0, 103.0, 104.0],
            "Volume": [1000, 2000, 3000],
        }, index=pd.date_range("2024-01-01", periods=3, freq="D"))

        mock_ctx = MagicMock()
        mock_ctx.override_df = df
        mock_ctx.engine_cfg = MagicMock()
        mock_ctx.engine_cfg.periods_per_year = 365
        mock_ctx.debug = False

        with pytest.raises(ValueError, match="NaN detected in OHLC"):
            _run_sim(mock_ctx)

    def test_zero_volume_detected(self):
        from antigravity_harness.gates import _run_sim

        df = pd.DataFrame({
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [95.0, 96.0, 97.0],
            "Close": [102.0, 103.0, 104.0],
            "Volume": [0, 0, 0],
        }, index=pd.date_range("2024-01-01", periods=3, freq="D"))

        mock_ctx = MagicMock()
        mock_ctx.override_df = df
        mock_ctx.engine_cfg = MagicMock()
        mock_ctx.engine_cfg.periods_per_year = 365
        mock_ctx.debug = False

        with pytest.raises(ValueError, match="zero-volume saturation"):
            _run_sim(mock_ctx)


# ─── Phase 5: CLI Containment ─────────────────────────────────────────

class TestCLISafeRun:
    """Verify _safe_run catches exceptions and exits cleanly."""

    def test_safe_run_catches_exception(self):
        from antigravity_harness.cli import _safe_run
        from antigravity_harness.phoenix import FlightRecorder
        FlightRecorder._instance = None

        def exploding_cmd(_args):
            raise RuntimeError("CLI BOOM")

        with pytest.raises(SystemExit) as exc_info:
            _safe_run(exploding_cmd, MagicMock())

        assert exc_info.value.code == 1
        FlightRecorder._instance = None

    def test_safe_run_passes_keyboard_interrupt(self):
        from antigravity_harness.cli import _safe_run

        def interrupted_cmd(_args):
            raise KeyboardInterrupt

        with pytest.raises(SystemExit) as exc_info:
            _safe_run(interrupted_cmd, MagicMock())

        assert exc_info.value.code == 130

    def test_safe_run_passes_system_exit(self):
        from antigravity_harness.cli import _safe_run

        def exiting_cmd(_args):
            sys.exit(42)

        with pytest.raises(SystemExit) as exc_info:
            _safe_run(exiting_cmd, MagicMock())

        assert exc_info.value.code == 42
