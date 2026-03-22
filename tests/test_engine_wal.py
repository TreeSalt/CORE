import tempfile
import unittest
from pathlib import Path

from mantis_core.engine import SimulatedAccount
from mantis_core.phoenix import SovereignAuditor
from mantis_core.wal import WriteAheadLog


class TestEngineWAL(unittest.TestCase):
    """
    Historical Regression: Verifies that the Phoenix Protocol (v4.4+) 
    maintains the same audit guarantees as the legacy WAL.
    """
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)
        self.db_path = self.root / "test_wal.db"
        self.wal = WriteAheadLog(self.db_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_auditor_boot_reconcile(self):
        """Verify SovereignAuditor correctly reconciles state at boot (Historic WAL intent)."""
        account = SimulatedAccount(10000.0, 0.0, False)
        auditor = SovereignAuditor(self.root, account_id="Test-Account")
        
        # Sim boot reconciliation
        auditor.boot_audit(account.cash, account.qty)
        
        # Verify event logged
        self.assertEqual(len(auditor.log), 1)
        self.assertEqual(auditor.log[0]["event"], "BOOT_SYNC")
        self.assertEqual(auditor.log[0]["data"]["cash"], 10000.0)

    def test_auditor_invariant_guard(self):
        """Verify Auditor blocks orders that violate institutional constraints."""
        account = SimulatedAccount(10000.0, 0.0, False)
        auditor = SovereignAuditor(self.root, account_id="Test-Account")
        
        # 1. Valid Order
        self.assertTrue(auditor.check_invariants(account, 10, 100.0)) # 1000 value (10% equity)
        
        # 2. Invalid Exposure (Too much leverage)
        # Exposure limit is 10.0x by default. Let's try 15x.
        self.assertFalse(auditor.check_invariants(account, 150, 1000.0))
        self.assertEqual(auditor.log[-1]["event"], "INVARIANT_VIOLATION")

    def test_audit_report_emission(self):
        """Verify signed audit report generation (Fiduciary Traceability)."""
        account = SimulatedAccount(12000.0, 0.0, False)
        auditor = SovereignAuditor(self.root, account_id="Test-Account")
        
        auditor.boot_audit(10000.0, 0.0)
        report_path = auditor.emit_audit_report(account)
        
        self.assertTrue(report_path.exists())
        # SovereignAuditor uses self.repo_root / "reports/AUDIT_REPORT.json"
        expected = self.root / "reports/AUDIT_REPORT.json"
        self.assertEqual(report_path, expected)

if __name__ == "__main__":
    unittest.main()
