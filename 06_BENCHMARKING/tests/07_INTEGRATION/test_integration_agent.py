"""
Benchmark Test Suite: 07_INTEGRATION
Domain: IntegrationAgent class
Ratified: 2026-03-09
"""
import pytest
from integration_domain.integration_agent import IntegrationAgent, CompatibilityReport


def test_required_imports_exist():
    from integration_domain.integration_agent import IntegrationAgent, CompatibilityReport
    assert IntegrationAgent is not None
    assert CompatibilityReport is not None


class TestIntegrationAgentInit:
    def test_initializes(self):
        ia = IntegrationAgent()
        assert ia is not None


class TestCompatibilityReport:
    def test_report_has_required_fields(self):
        report = CompatibilityReport(
            compatible=True,
            mismatches=[],
            domain_a="01_DATA_INGESTION",
            domain_b="02_RISK_MANAGEMENT"
        )
        assert report.compatible is True
        assert report.domain_a == "01_DATA_INGESTION"

    def test_report_serializable(self):
        report = CompatibilityReport(
            compatible=True,
            mismatches=[],
            domain_a="01_DATA_INGESTION",
            domain_b="02_RISK_MANAGEMENT"
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "compatible" in d


class TestInterfaceVerification:
    def setup_method(self):
        self.ia = IntegrationAgent()

    def test_check_returns_compatibility_report(self, tmp_path):
        p1 = tmp_path / "PROPOSAL_A.md"
        p1.write_text("```python\nclass HandlerA:\n    def process(self, data: dict) -> dict:\n        pass\n```")
        p2 = tmp_path / "PROPOSAL_B.md"
        p2.write_text("```python\nclass HandlerB:\n    def process(self, data: dict) -> dict:\n        pass\n```")
        result = self.ia.check(str(p1), "01_DATA_INGESTION", str(p2), "02_RISK_MANAGEMENT")
        assert isinstance(result, CompatibilityReport)

    def test_rejects_same_domain(self, tmp_path):
        p = tmp_path / "PROPOSAL.md"
        p.write_text("```python\npass\n```")
        with pytest.raises((ValueError, SystemExit)):
            self.ia.check(str(p), "01_DATA_INGESTION", str(p), "01_DATA_INGESTION")

    def test_rejects_governance_domain(self, tmp_path):
        p = tmp_path / "PROPOSAL.md"
        p.write_text("```python\npass\n```")
        with pytest.raises((ValueError, SystemExit)):
            self.ia.check(str(p), "04_GOVERNANCE", str(p), "01_DATA_INGESTION")


class TestFiduciaryConstraints:
    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("07_INTEGRATION/integration_domain/integration_agent.py").read_text().lower()
        for keyword in ['password =', 'api_key =', 'secret =']:
            assert keyword not in src

    def test_no_governance_imports(self):
        import ast
        import pathlib
        src = pathlib.Path("07_INTEGRATION/integration_domain/integration_agent.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, 'module', '') or ''
                assert '04_GOVERNANCE' not in mod
