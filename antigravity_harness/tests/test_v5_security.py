import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()

class TestV5Security(unittest.TestCase):
    def setUp(self):
        self.test_dir = REPO_ROOT / "tmp_security_test"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_vuln_scanner_detects_shell_true(self):
        bad_code = "import subprocess\nsubprocess.run('ls', shell=True)\n"
        test_file = self.test_dir / "bad_shell.py"
        test_file.write_text(bad_code)
        
        cmd = ["python3", "-B", str(REPO_ROOT / "scripts/vuln_scanner.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, check=False)
        self.assertIn("[SHELL] Risky 'shell=True'", result.stdout)
        self.assertEqual(result.returncode, 1)

    def test_vuln_scanner_detects_unsafe_import(self):
        bad_code = "import pickle\n"
        test_file = self.test_dir / "bad_import.py"
        test_file.write_text(bad_code)
        
        result = subprocess.run(["python3", "-B", str(REPO_ROOT / "scripts/vuln_scanner.py")], 
                               capture_output=True, text=True, cwd=REPO_ROOT, check=False)
        self.assertIn("[IMPORT] Unsafe module 'pickle'", result.stdout)

    def test_vuln_scanner_detects_secrets(self):
        bad_code = "SECRET = 'aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890/=='\n" # high entropy
        # Note: We need to make sure this is NOT in a file named '*test*' or in 'tests/' 
        # because the scanner now skips tests for secrets.
        # But wait, tmp_security_test is in REPO_ROOT/tmp_security_test which has 'test' in it.
        # Let's use a different name for the temp dir.
        
        secret_test_dir = REPO_ROOT / "tmp_sec_scan"
        secret_test_dir.mkdir(exist_ok=True)
        try:
            bad_file = secret_test_dir / "shadow.py"
            bad_file.write_text(bad_code)
            result = subprocess.run(["python3", "-B", str(REPO_ROOT / "scripts/vuln_scanner.py")], 
                                   capture_output=True, text=True, cwd=REPO_ROOT, check=False)
            self.assertIn("[SECRET] Potential high-entropy target", result.stdout)
        finally:
            if secret_test_dir.exists():
                shutil.rmtree(secret_test_dir)

    def test_self_heal_untracked_guard(self):
        shadow_file = REPO_ROOT / "antigravity_harness/shadow_persist.py"
        shadow_file.write_text("print('persistence')")
        
        try:
            result = subprocess.run(["python3", "-B", str(REPO_ROOT / "scripts/self_heal.py")], 
                                   capture_output=True, text=True, cwd=REPO_ROOT, check=False)
            self.assertIn("SECURITY VIOLATION: Untracked executables", result.stdout)
            self.assertEqual(result.returncode, 1)
        finally:
            if shadow_file.exists():
                shadow_file.unlink()

if __name__ == "__main__":
    unittest.main()
