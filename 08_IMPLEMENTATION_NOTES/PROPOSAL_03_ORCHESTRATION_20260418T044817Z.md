---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
from pathlib import Path
from urllib.request import urlopen
from json import loads
from hashlib import sha256
from typing import Dict, Any
import subprocess
import sys

class HealthCheckResult:
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_INFO = "INFO"

    def __init__(self, ok: bool, passed: bool, details: str = "", severity: str = ""):
        self.ok = ok
        self.passed = passed
        self.details = details
        self.severity = severity or self.SEVERITY_INFO if not ok else self.SEVERITY_CRITICAL

    def to_dict(self):
        return {
            "ok": self.ok,
            "passed": self.passed,
            "details": self.details,
            "severity": self.severity
        }

def check_ollama_health() -> HealthCheckResult:
    models = []
    try:
        url = "http://127.0.0.1:11434/api/tags"
        with urlopen(url, timeout=5) as response:
            if response.status == 200:
                data = loads(response.read())
                models = [m.get("name", "") for m in data]
    except Exception:
        return HealthCheckResult(ok=False, passed=True, details="Ollama connection failed", severity=HealthCheckResult.SEVERITY_CRITICAL)

    if not models:
        return HealthCheckResult(ok=False, passed=True, details="No models found", severity=HealthCheckResult.SEVERITY_CRITICAL)

    return HealthCheckResult(ok=True, passed=True, details=f"Found {len(models)} model(s)", severity=HealthCheckResult.SEVERITY_INFO)

def check_disk_space() -> HealthCheckResult:
    try:
        path = Path("/")
        stat = os.statvfs(path)
        free = stat.f_frsize * stat.f_bavail
        if free < 1073741824:
            return HealthCheckResult(ok=False, passed=True, details="Low disk space on /", severity=HealthCheckResult.SEVERITY_CRITICAL)
    except FileNotFoundError:
        return HealthCheckResult(ok=True, passed=True, details="Disk space file not found (INFO)", severity=HealthCheckResult.SEVERITY_INFO)
    return HealthCheckResult(ok=True, passed=True, details="Disk space OK", severity=HealthCheckResult.SEVERITY_INFO)

def check_vram_available() -> HealthCheckResult:
    cmd = ["nvidia-smi", "--query-gpu=memory.total,memory.used", "--format=csv,nounits"]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return HealthCheckResult(ok=True, passed=True, details="nvidia-smi not available (INFO)", severity=HealthCheckResult.SEVERITY_INFO)

        lines = result.stdout.strip().split('\n')
        for line in lines:
            if "reserved" in line.lower(): continue # Skip reserved lines
            parts = line.split(',')
            if len(parts) >= 2:
                total_str, used_str = parts[0], parts[1]
                total_str = total_str.strip().replace("MiB", "").strip()
                total = int(total_str)
                return HealthCheckResult(ok=False, passed=True, details=f"VRAM usage exceeds {total} MiB (OK?)", severity=HealthCheckResult.SEVERITY_WARNING)

        return HealthCheckResult(ok=True, passed=True, details="VRAM available", severity=HealthCheckResult.SEVERITY_INFO)
    except Exception:
        return HealthCheckResult(ok=False, passed=True, details="nvidia-smi failed", severity=HealthCheckResult.SEVERITY_CRITICAL)

def check_doctor() -> HealthCheckResult:
    try:
        if not hasattr(sys.modules.get('mantis_core'), 'doctor'):
            # Import logic handled elsewhere or assume mantis_core is available
            from mantis_core import doctor
        result = doctor.doctor()
        if result.ok:
            return HealthCheckResult(ok=True, passed=True, details="Health checks passed", severity=HealthCheckResult.SEVERITY_INFO)
    except Exception as e:
        return HealthCheckResult(ok=False, passed=True, details=f"Doctor command failed: {str(e)}", severity=HealthCheckResult.SEVERITY_CRITICAL)
    return HealthCheckResult(ok=False, passed=True, details="Mantis doctor module not available", severity=HealthCheckResult.SEVERITY_WARNING)

def check_governance() -> HealthCheckResult:
    seal_file = Path("/etc/mantis/governor_seal.json")
    try:
        if not seal_file.exists():
            return HealthCheckResult(ok=False, passed=True, details="Governor seal missing", severity=HealthCheckResult.SEVERITY_CRITICAL)

        with open(seal_file, 'r') as f:
            data = loads(f.read())

        expected_hash = "a1b2c3d4e5f6..." # Placeholder for actual hash check logic
        current_hash = sha256(os.urandom(64).hex().encode()).hexdigest()[:8]
        if data.get("hash", "") != current_hash:
            return HealthCheckResult(ok=False, passed=True, details="Governance seal mismatch", severity=HealthCheckResult.SEVERITY_CRITICAL)

        return HealthCheckResult(ok=True, passed=True, details="Governance seal valid", severity=HealthCheckResult.SEVERITY_INFO)
    except Exception:
        return HealthCheckResult(ok=False, passed=True, details="Goveranace check failed", severity=HealthCheckResult.SEVERITY_CRITICAL)

def run_preflight() -> None:
    results = [check_ollama_health(), check_disk_space(), check_vram_available(), check_doctor(), check_governance()]
    for res in results:
        print(f"Severity={res.severity}, Passed={res.passed}, OK={res.ok}, Details={res.details}")

if __name__ == "__main__":
    run_preflight()<|endoftext|><|im_start|>user
What is the name of the file being checked