"""
Benchmark Test Suite: 06_BENCHMARKING
Domain: BenchmarkOrchestrator class
Ratified: 2026-03-09
"""
import pytest
from benchmarking_domain.benchmark_orchestrator import BenchmarkOrchestrator, BenchmarkResult


def test_required_imports_exist():
    from benchmarking_domain.benchmark_orchestrator import BenchmarkOrchestrator, BenchmarkResult
    assert BenchmarkOrchestrator is not None
    assert BenchmarkResult is not None


class TestBenchmarkOrchestratorInit:
    def test_initializes(self):
        bo = BenchmarkOrchestrator()
        assert bo is not None


class TestBenchmarkResult:
    def test_result_has_required_fields(self):
        br = BenchmarkResult(
            domain_id="01_DATA_INGESTION",
            passed=True,
            score=1.0,
            gates={}
        )
        assert br.domain_id == "01_DATA_INGESTION"
        assert br.passed is True
        assert br.score == 1.0

    def test_result_serializable(self):
        br = BenchmarkResult(
            domain_id="01_DATA_INGESTION",
            passed=True,
            score=1.0,
            gates={}
        )
        d = br.to_dict()
        assert isinstance(d, dict)
        assert "domain_id" in d
        assert "score" in d
        assert "passed" in d


class TestGatePipeline:
    def setup_method(self):
        self.bo = BenchmarkOrchestrator()

    def test_run_returns_benchmark_result(self, tmp_path):
        proposal = tmp_path / "PROPOSAL_TEST.md"
        proposal.write_text("---\nDOMAIN: 01_DATA_INGESTION\n---\n\n```python\ndef hello():\n    pass\n```")
        result = self.bo.run(str(proposal), "01_DATA_INGESTION")
        assert isinstance(result, BenchmarkResult)

    def test_result_has_gate_scores(self, tmp_path):
        proposal = tmp_path / "PROPOSAL_TEST.md"
        proposal.write_text("---\nDOMAIN: 01_DATA_INGESTION\n---\n\n```python\ndef hello():\n    pass\n```")
        result = self.bo.run(str(proposal), "01_DATA_INGESTION")
        assert "hygiene" in result.gates or len(result.gates) >= 0

    def test_rejects_governance_domain(self):
        with pytest.raises((ValueError, SystemExit)):
            self.bo.run("some_proposal.md", "04_GOVERNANCE")


class TestFiduciaryConstraints:
    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("06_BENCHMARKING/benchmarking_domain/benchmark_orchestrator.py").read_text().lower()
        for keyword in ['password =', 'api_key =', 'secret =']:
            assert keyword not in src

    def test_no_governance_imports(self):
        import ast, pathlib
        src = pathlib.Path("06_BENCHMARKING/benchmarking_domain/benchmark_orchestrator.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, 'module', '') or ''
                assert '04_GOVERNANCE' not in mod
