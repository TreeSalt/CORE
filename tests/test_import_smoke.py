import importlib
import pkgutil
import sys
import unittest
from pathlib import Path

# Adjust path to find the package if run from root or tests/
# We assume this file is in <ROOT>/tests/
# and package is in <ROOT>/mantis_core/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import mantis_core  # noqa: E402


class TestImportSmoke(unittest.TestCase):
    """
    Task 6.1: Import Smoke Test
    Dynamically discover and import all modules in mantis_core
    to ensure no static NameErrors or SyntaxErrors exist.
    """

    def test_all_modules_importable(self):
        """Walk package and import every module found."""
        package = mantis_core
        path = package.__path__
        prefix = package.__name__ + "."

        failures = []

        # Walk recursively
        for _, name, _is_pkg in pkgutil.walk_packages(path, prefix):
            try:
                importlib.import_module(name)
            except Exception as e:
                failures.append(f"{name}: {e}")

        if failures:
            self.fail(f"Failed to import {len(failures)} modules:\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
