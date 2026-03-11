"""
Benchmark Test Suite: 05_REPORTING
Domain: ReportGenerator class
Ratified: 2026-03-09
"""
from pathlib import Path
from reporting_domain.report_generator import ReportGenerator


def test_required_imports_exist():
    from reporting_domain.report_generator import ReportGenerator
    assert ReportGenerator is not None


class TestReportGeneratorInit:
    def test_initializes_with_output_dir(self, tmp_path):
        rg = ReportGenerator(output_dir=str(tmp_path))
        assert rg.output_dir == str(tmp_path)


class TestReportGeneration:
    def setup_method(self, tmp_path=None):
        import tempfile
        self.tmp_dir = tempfile.mkdtemp()
        self.rg = ReportGenerator(output_dir=self.tmp_dir)
        self.sample_result = {
            "domain": "01_DATA_INGESTION",
            "model": "qwen2.5-coder:7b",
            "tier": "sprinter",
            "score": 1.0,
            "gates": {
                "hygiene": {"passed": True, "score": 1.0},
                "hallucination": {"passed": True, "score": 1.0},
                "logic": {"passed": True, "score": 1.0}
            },
            "timestamp": "2026-03-09T19:00:00Z"
        }

    def test_generate_returns_filepath(self):
        path = self.rg.generate(self.sample_result)
        assert path is not None
        assert Path(path).exists()

    def test_report_contains_domain_name(self):
        path = self.rg.generate(self.sample_result)
        content = Path(path).read_text()
        assert "01_DATA_INGESTION" in content

    def test_report_contains_score(self):
        path = self.rg.generate(self.sample_result)
        content = Path(path).read_text()
        assert "1.0" in content

    def test_report_contains_model(self):
        path = self.rg.generate(self.sample_result)
        content = Path(path).read_text()
        assert "qwen2.5-coder:7b" in content

    def test_report_contains_timestamp(self):
        from datetime import datetime
        path = self.rg.generate(self.sample_result)
        content = Path(path).read_text()
        current_date_prefix = datetime.now().strftime("%Y-%m")
        assert current_date_prefix in content

    def test_report_is_markdown(self):
        path = self.rg.generate(self.sample_result)
        assert path.endswith(".md")

    def test_report_written_to_output_dir(self):
        path = self.rg.generate(self.sample_result)
        assert str(self.tmp_dir) in path


class TestFiduciaryConstraints:
    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("05_REPORTING/reporting_domain/report_generator.py").read_text().lower()
        for keyword in ['password', 'api_key', 'secret', 'token']:
            assert f'{keyword} =' not in src

    def test_no_governance_domain_writes(self):
        import ast
        import pathlib
        src = pathlib.Path("05_REPORTING/reporting_domain/report_generator.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, 'module', '') or ''
                assert '04_GOVERNANCE' not in mod
