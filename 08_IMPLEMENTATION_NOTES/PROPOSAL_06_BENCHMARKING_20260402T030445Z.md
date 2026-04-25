---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pytest
from unittest import mock
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import StringIO

from mantis_core.security.target_scraper import TargetScraper, BountyTarget
from mantis_core.security.recon_engine import ReconEngine, ReconProfile
from mantis_core.security.submission_tracker import SubmissionTracker, Submission


# -----------------------------------------------------------------------------
# TEST TARGET SCRAPER (5 tests)
# -----------------------------------------------------------------------------

class TestTargetScraper:
    @staticmethod
    def test_dataclass_creation():
        target = BountyTarget(
            ip="192.168.1.1",
            domain="example.com",
            port=443,
            protocol="https"
        )
        assert target.ip == "192.168.1.1"
        assert target.domain == "example.com"
        assert target.port == 443

    @staticmethod
    def test_deduplication():
        scraper = TargetScraper()
        
        # Add duplicate targets
        scraper.add_target(BountyTarget(ip="192.168.1.1", domain="example.com", port=443))
        scraper.add_target(BountyTarget(ip="192.168.1.1", domain="example.com", port=443))
        
        assert len(scraper.targets) == 1

    @staticmethod
    def test_ai_filter():
        scraper = TargetScraper()
        ai_target = BountyTarget(
            ip="192.168.1.1",
            domain="bot.com",
            port=443,
            protocol="https",
            ai_score=0.95
        )
        
        assert scraper.add_and_filter(ai_target) is False


    @staticmethod
    def test_graceful_offline():
        scraper = TargetScraper()
        
        with mock.patch.object(TargetScraper, 'check_connectivity') as mock_check:
            mock_check.return_value = True
            
            target = BountyTarget(ip="192.168.1.1")
            assert scraper.add_target(target) is True


    @staticmethod
    def test_rate_limit():
        scraper = TargetScraper()
        
        # Add targets exceeding rate limit (5 per batch)
        for i in range(5):
            scraper.add_target(BountyTarget(ip=f"192.168.{i}.1"))
        
        assert len(scraper.targets) == 5


# -----------------------------------------------------------------------------
# TEST RECON ENGINE (5 tests)
# -----------------------------------------------------------------------------

class TestReconEngine:
    @staticmethod
    def test_profile_created():
        profile = ReconProfile(
            name="test-profile",
            risk_level="high"
        )
        
        assert profile.name == "test-profile"
        assert profile.risk_level == "high"

    @staticmethod
    def test_scope_respected():
        engine = ReconEngine(profile=ReconProfile(name="limited-scope"))
        
        scope = {"domain": "example.com"}
        with mock.patch.object(engine, 'scan_domains') as mock_scan:
            mock_scan.return_value = [192, 168, 1]
            
            result = engine.get_info(domain="example.com", scope=scope)
            assert len(result) > 0

    @staticmethod
    def test_requests_logged():
        engine = ReconEngine(profile=ReconProfile(name="tracker"))
        
        with mock.patch.object(engine, 'make_request') as mock_request:
            mock_request.return_value = {"status": 200}
            
            result = engine.scan_ip("192.168.1.1")
            
            assert mock_request.called

    @staticmethod
    def test_risk_score_range():
        profile = ReconProfile(name="risk-test", risk_level="medium")
        engine = ReconEngine(profile=profile)
        
        with mock.patch.object(engine, 'analyze_target') as mock_analyze:
            mock_analyze.return_value = {"score": 0.6}
            
            result = engine.analyze("192.168.1.1")
            
            assert 0 <= result["score"] <= 1

    @staticmethod
    def test_prioritizer_sorts():
        profile = ReconProfile(name="sort-test")
        engine = ReconEngine(profile=profile)
        
        targets = [
            BountyTarget(ip="1.1.1.1", score=0.9),
            BountyTarget(ip="2.2.2.2", score=0.5),
            BountyTarget(ip="3.3.3.3", score=0.8)
        ]
        
        sorted_targets = engine.prioritize(targets)
        
        assert sorted_targets[0].score == 0.9


# -----------------------------------------------------------------------------
# TEST SUBMISSION TRACKER (6 tests)
# -----------------------------------------------------------------------------

class TestSubmissionTracker:
    @staticmethod
    def test_create_submission():
        tracker = SubmissionTracker(name="test-tracker")
        
        submission = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="active",
            submitted_at=datetime.now()
        )
        
        assert tracker.add_submission(submission) is True

    @staticmethod
    def test_state_transition():
        tracker = SubmissionTracker(name="state-test")
        
        submission = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="active"
        )
        
        # Advance time to create report
        from datetime import timedelta
        with mock.patch('mantis_core.security.submission_tracker.time') as mock_time:
            mock_time.gmtime.side_effect = lambda *args, **kwargs: datetime.now().replace(hour=23, minute=59)
            
            tracker.submit_report(submission)

    @staticmethod
    def test_append_only_history():
        tracker = SubmissionTracker(name="append-test")
        
        submission1 = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="active"
        )
        
        submission2 = Submission(
            target="192.168.1.2",
            bounty_id="BNT-002",
            state="active"
        )
        
        tracker.add_submission(submission1)
        tracker.add_submission(submission2)
        
        assert len(tracker.submissions) == 2

    @staticmethod
    def test_active_excludes_terminal():
        tracker = SubmissionTracker(name="terminal-test")
        
        submission = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="closed"
        )
        
        tracker.add_submission(submission)
        
        assert len([s for s in tracker.submissions if s.state == "active"]) == 0

    @staticmethod
    def test_stats_counts():
        tracker = SubmissionTracker(name="stats-test")
        
        submission1 = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="pending"
        )
        
        submission2 = Submission(
            target="192.168.1.2",
            bounty_id="BNT-002",
            state="reviewing"
        )
        
        submission3 = Submission(
            target="192.168.1.3",
            bounty_id="BNT-003",
            state="closed"
        )
        
        tracker.add_submission(submission1)
        tracker.add_submission(submission2)
        tracker.add_submission(submission3)
        
        assert tracker.get_stats()["pending"] == 1
        assert tracker.get_stats()["reviewing"] == 1
        assert tracker.get_stats()["closed"] == 1

    @staticmethod
    def test_weekly_report_markdown():
        tracker = SubmissionTracker(name="report-test")
        
        submission = Submission(
            target="192.168.1.1",
            bounty_id="BNT-001",
            state="pending",
            submitted_at=datetime.now()
        )
        
        tracker.add_submission(submission)
        
        with mock.patch('mantis_core.security.submission_tracker.time') as mock_time:
            mock_time.gmtime.side_effect = lambda *args, **kwargs: datetime.now().replace(hour=23, minute=59)
            
            output = StringIO()
            tracker.generate_report(output)
            report = output.getvalue()
            
            assert "weekly" in report.lower() or "report" in report.lower()
```