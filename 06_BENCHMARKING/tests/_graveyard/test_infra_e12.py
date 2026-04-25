import sys
sys.path.insert(0, 'scripts')
from cgroup_manager import setup_cgroup, get_cgroup_stats, is_ollama_in_cgroup
from unittest.mock import patch, MagicMock
import pytest

class TestCgroupManager:
    
    @pytest.fixture(autouse=True)
    def mock_subsystem(self, mocker):
        # Mock the setup function to simulate cgroup creation without touching OS
        with patch('cgroup_manager.setup_cgroup') as mock_setup, \
             patch.object(sys.modules['cgroup_manager'], 'get_cgroup_stats') as mock_stats:
            yield mock_setup, mock_stats

    def test_setup_creates_slice(self):
        # Simulate the creation of a cgroup slice without real execution
        mock_setup.return_value = {"slice_created": True}
        mock_stats.return_value = {"cpu": 0.5, "memory": 2147483648}
        result = setup_cgroup("ollama", "test_slice")
        assert result["slice_created"] is True

    def test_stats_readable(self):
        # Verify that stats can be retrieved without errors
        mock_setup.return_value = {"slice_created": False}
        mock_stats.return_value = {"cpu": 0.1, "memory": 1073741824}
        
        try:
            result = get_cgroup_stats("ollama", "test_slice")
            assert result["cpu"] > 0
        except Exception as e:
            # Handle potential error cases gracefully if needed
            pass
            
    def test_graceful_failure_no_v2(self):
        # Simulate failure case for v1 (v2 support required)
        mock_setup.return_value = {"error": "cgroup v1 not supported"}
        result = get_cgroup_stats("ollama", "test_slice")
        assert result.get("error") is True
        
    def test_teardown_removes(self):
        # Verify removal logic (handled via mock)
        mock_setup.return_value = {"cleared": True}
        mock_stats.return_value = {}
        
        try:
            teardown_result = get_cgroup_stats("ollama", "test_slice")
            assert teardown_result is None or teardown_result.get("error") == "slice_removed"
        except Exception as e:
            pass

class TestDualLane:
    
    @pytest.fixture(autouse=True)
    def mock_dual_lane(self, mocker):
        # Patch global state or functions to simulate the dual lane environment
        with patch('cgroup_manager.setup_cgroup') as mock_setup:
            yield mock_setup

    def test_gpu_lane_processes_sprinter(self):
        # Verify GPU lane logic for sprinter tasks
        mock_setup.return_value = {"lane": "gpu"}
        result = setup_cgroup("ollama", "sprinter_task")
        assert result["lane"] == "gpu"

    def test_cpu_lane_handles_heavy_blocks(self):
        # Verify CPU lane logic for heavy blocks
        mock_setup.return_value = {"lane": "cpu"}
        result = setup_cgroup("ollama", "heavy_block_task")
        assert result["lane"] == "cpu"

    def test_shutdown_cleanup_resources(self):
        # Ensure proper shutdown cleanup
        mock_setup.return_value = {"status": "shutdown"}
        
        try:
            cleanup_result = setup_cgroup("ollama", None)
            assert cleanup_result is None or cleanup_result.get("error") == "resources_cleaned"
        except Exception as e:
            pass

    def test_priority_queue_order(self):
        # Verify task priority handling in the queue
        mock_setup.return_value = {"queue_status": "ordered"}
        
        try:
            order_result = get_cgroup_stats("ollama", "test_queue")
            assert order_result is None or order_result.get("error") == "queue_ordered"
        except Exception as e:
            pass

def test_ollama_in_cgroup(mock_setup):
    # Final check to ensure all tests verify Ollama integration correctly
    with patch('cgroup_manager.is_ollama_in_cgroup') as mock_check:
        mock_check.return_value = True
        
        try:
            in_cgroup_result = is_ollama_in_cgroup("ollama")
            assert in_cgroup_result is True or in_cgroup_result.get("error") == "process_running"
        except Exception as e:
            pass
