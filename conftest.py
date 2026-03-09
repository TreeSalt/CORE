import sys
from pathlib import Path

repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "01_DATA_INGESTION"))
sys.path.insert(0, str(repo_root / "02_RISK_MANAGEMENT"))
sys.path.insert(0, str(repo_root / "03_ORCHESTRATION"))
sys.path.insert(0, str(repo_root / "05_REPORTING"))
sys.path.insert(0, str(repo_root / "06_BENCHMARKING"))
sys.path.insert(0, str(repo_root / "07_INTEGRATION"))
sys.path.insert(0, str(repo_root / "08_CYBERSECURITY"))
sys.path.insert(0, str(repo_root / "00_PHYSICS_ENGINE"))
