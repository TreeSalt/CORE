---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import pytest
from mantis_core.orchestration.mission_preflight import PreflightResult, validate_governance_path
from mantis_core.orchestration.oscillation_detector import OscillationDetector, PlateauThreshold
from mantis_core.orchestration.core_doctor import CoreDoctor
from tempfile import NamedTemporaryFile

class TestMissionPreflight:
    def test_valid_brief(self):
        result = validate_governance_path("valid", "mantis://core")
        assert result is True
    
    def test_missing_domain(self):
        result = validate_governance_path("invalid", "missing://domain")
        assert result is False
    
    def test_governance_path_rejected(self):
        result = validate_governance_path("rejected", "mantis://restricted/path")
        assert result is False

    def test_empty_brief(self):
        result = validate_governance_path("", "")
        assert result is False
    
    def test_hash_computed(self):
        hash_val = PreflightResult.compute_hash("brief_content")
        assert isinstance(hash_val, str) and len(hash_val) > 0
    
    def test_invalid_extension_warns(self):
        with NamedTemporaryFile(suffix=".txt") as f:
            pass
        
class TestOscillationDetector:
    def test_no_os_1st_attempt(self):
        detector = OscillationDetector(PlateauThreshold(3))
        scores = [10, 20, 30]
        assert not detector.check(scores)
    
    def test_os_after_3_same_gate(self):
        detector = OscillationDetector(PlateauThreshold(3))
        scores = [10, 20, 20, 20]
        assert detector.check(scores)
    
    def test_plateau_identical_scores(self):
        detector = OscillationDetector(PlateauThreshold(5))
        scores = [10, 10, 10, 10, 10]
        assert detector.check(scores)
    
    def test_directive_generated(self):
        detector = OscillationDetector()
        directive = detector.generate_directive("oscillating")
        assert isinstance(directive, str) and "OSCILLATION" in directive
    
    def test_diff_gates_no_trigger(self):
        detector = OscillationDetector(PlateauThreshold(2))
        scores = [10, 20, 30, 40]
        assert not detector.check(scores)

class TestCoreDoctorImport:
    def test_importable(self):
        doctor = CoreDoctor()
        assert doctor is not None
    
    def test_structured_report(self):
        report = doctor.generate_report("mock_id")
        assert isinstance(report, dict)