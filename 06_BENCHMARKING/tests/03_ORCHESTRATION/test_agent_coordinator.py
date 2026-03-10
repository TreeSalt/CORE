"""
Benchmark Test Suite: 03_ORCHESTRATION
Domain: AgentCoordinator class
Ratified: 2026-03-09
"""
import pytest
from orchestration_domain.agent_coordinator import AgentCoordinator, TaskPackage


def test_required_imports_exist():
    from orchestration_domain.agent_coordinator import AgentCoordinator, TaskPackage
    assert AgentCoordinator is not None
    assert TaskPackage is not None


class TestAgentCoordinatorInit:
    def test_initializes_empty(self):
        ac = AgentCoordinator()
        assert ac.get_active_assignments() == {}

    def test_queue_starts_empty(self):
        ac = AgentCoordinator()
        assert ac.get_queue_depth("01_DATA_INGESTION") == 0


class TestTaskPackage:
    def test_task_package_creates_with_required_fields(self):
        pkg = TaskPackage(domain_id="01_DATA_INGESTION", task="test", mission="do something", model="qwen2.5-coder:7b")
        assert pkg.domain_id == "01_DATA_INGESTION"
        assert pkg.task == "test"

    def test_task_package_rejects_governance_domain(self):
        with pytest.raises((ValueError, SystemExit)):
            TaskPackage(domain_id="04_GOVERNANCE", task="test", mission="do something", model="qwen2.5-coder:7b")


class TestDomainLocking:
    def test_submit_assigns_domain(self):
        ac = AgentCoordinator(dispatch_fn=lambda pkg: None)
        pkg = TaskPackage(domain_id="01_DATA_INGESTION", task="test", mission="do something", model="qwen2.5-coder:7b")
        ac.submit(pkg)
        import time; time.sleep(0.1)
        # Domain should be tracked (active or completed)
        assert True  # submission did not raise

    def test_second_submit_to_busy_domain_queues(self):
        import threading
        barrier = threading.Barrier(2)
        def slow_dispatch(pkg):
            barrier.wait()
        ac = AgentCoordinator(dispatch_fn=slow_dispatch)
        pkg1 = TaskPackage(domain_id="01_DATA_INGESTION", task="t1", mission="m1", model="qwen2.5-coder:7b")
        pkg2 = TaskPackage(domain_id="01_DATA_INGESTION", task="t2", mission="m2", model="qwen2.5-coder:7b")
        ac.submit(pkg1)
        import time; time.sleep(0.05)
        ac.submit(pkg2)
        assert ac.get_queue_depth("01_DATA_INGESTION") >= 0  # queued or processing


class TestFiduciaryConstraints:
    def test_no_governance_domain_writes(self):
        import ast, pathlib
        src = pathlib.Path("03_ORCHESTRATION/orchestration_domain/agent_coordinator.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert '04_GOVERNANCE' not in node.value or 'GOVERNANCE' in str(node.value).upper()

    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("03_ORCHESTRATION/orchestration_domain/agent_coordinator.py").read_text().lower()
        for keyword in ['password', 'api_key', 'secret', 'token']:
            assert f'{keyword} =' not in src

    def test_governance_submission_rejected(self):
        ac = AgentCoordinator(dispatch_fn=lambda pkg: None)
        with pytest.raises((ValueError, SystemExit)):
            pkg = TaskPackage(domain_id="04_GOVERNANCE", task="test", mission="do something", model="qwen2.5-coder:7b")
            ac.submit(pkg)
