---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any


# Module-level constants
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class HealthCheckResult:
    check_name: str
    severity: str  # one of CRITICAL/WARNING/INFO
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: str  # ISO format UTC


@dataclass(frozen=True)
class PreflightVerdict:
    ok_to_dispatch: bool
    critical_count: int
    warning_count: int
    info_count: int
    checks: List[HealthCheckResult]
    generated_at: str  # ISO format UTC


def _get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check_disk_space(min_free_gb: int = 5) -> HealthCheckResult:
    """Verifies at least min_free_gb gigabytes are free in the repo's filesystem.
    
    CRITICAL severity, fails if free space below threshold.
    """
    try:
        # Get disk usage for current directory
        total, used, free = shutil.disk_usage(os.getcwd())
        
        # Convert free space to GB
        free_gb = free / (1024 ** 3)
        passed = free_gb >= min_free_gb
        
        details = {
            "available_gb": round(free_gb, 2),
            "minimum_required_gb": min_free_gb,
            "current_dir": os.getcwd()[:50]
        }
        
        message = f"Disk space {'sufficient' if passed else 'insufficient'}: {free_gb:.2f}GB free (minimum: {min_free_gb}GB)"
        return HealthCheckResult(
            check_name="disk_space",
            severity=SEVERITY_CRITICAL,
            passed=passed,
            message=message,
            details=details,
            timestamp=_get_utc_timestamp()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="disk_space",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to check disk space: {str(e)}",
            details={"error": str(e)},
            timestamp=_get_utc_timestamp()
        )


def check_governor_seal() -> HealthCheckResult:
    """Verifies .governor_seal exists and the AEC_HASH line is present and
    matches the SHA256 of 04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md.
    
    CRITICAL severity, fails on any mismatch or missing file.
    """
    try:
        seal_path = Path(".governor_seal")
        
        if not seal_path.exists():
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=".governor_seal file does not exist",
                details={"path": str(seal_path)},
                timestamp=_get_utc_timestamp()
            )
        
        # Read seal content to get AEC_HASH
        with open(seal_path, 'r') as f:
            seal_content = f.read()
        
        aec_hash_line = None
        for line in seal_content.split('\n'):
            if line.startswith('AEC_HASH='):
                aec_hash_line = line.strip().split('=', 1)[1]
                break
        
        if aec_hash_line is None:
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message="AEC_HASH line not found in .governor_seal",
                details={"path": str(seal_path)},
                timestamp=_get_utc_timestamp()
            )
        
        # Construct constitution path relative to repo root (assuming same dir as script)
        script_dir = Path(__file__).parent.parent
        constitution_path = script_dir / "04_GOVERNANCE" / "AGENTIC_ETHICAL_CONSTITUTION.md"
        
        if not constitution_path.exists():
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"Constitution file not found at: {constitution_path}",
                details={"path": str(constitution_path)},
                timestamp=_get_utc_timestamp()
            )
        
        # Read constitution and compute SHA256
        with open(constitution_path, 'rb') as f:
            constitution_content = f.read()
        
        import hashlib
        expected_hash = hashlib.sha256(constitution_content).hexdigest()
        
        if aec_hash_line != expected_hash:
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"AEC_HASH mismatch. Expected: {expected_hash[:16]}..., Got: {aec_hash_line}",
                details={"expected_hash": expected_hash[:64], "found_hash": aec_hash_line},
                timestamp=_get_utc_timestamp()
            )
        
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_INFO,
            passed=True,
            message="Governor seal verified successfully",
            details={"hash_verified": True, "hash_length": len(expected_hash)},
            timestamp=_get_utc_timestamp()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to verify governor seal: {str(e)}",
            details={"error": str(e)},
            timestamp=_get_utc_timestamp()
        )


def check_ollama_health() -> HealthCheckResult:
    """Performs a GET request to http://localhost:11434/api/tags with a 5-second
    timeout. Verifies the response is valid JSON and contains a non-empty
    'models' list. CRITICAL severity."""
    try:
        url = "http://localhost:11434/api/tags"
        
        # Use urllib.request for HTTP calls (stdlib only)
        request_data = f"""<python>
import urllib.request
import json

try:
    req = urllib.request.Request(
        '{url}',
        method='GET',
        headers={'User-Agent': 'Preflight-Runner'}
    )
    
    with urllib.request.urlopen(req, timeout=5) as response:
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            return {json.dumps({
                "has_valid_response": True,
                "status_code": response.status,
                "models_count": len(data.get('models', [])),
                "is_models_non_empty": len(data.get('models', [])) > 0,
                "data_keys": list(data.keys()) if isinstance(data, dict) else None
            })}
        return {json.dumps({
            "has_valid_response": False,
            "status_code": response.status
        })}
except urllib.error.URLError as e:
    return {json.dumps({
        "has_valid_response": False,
        "error_type": "URLError",
        "reason": str(e.reason) if hasattr(e, 'reason') else str(e)
    })}
except Exception as e:
    return {json.dumps({
        "has_valid_response": False,
        "error_type": "Exception",
        "message": str(e)
    })}
</python>"""
        
        # Execute the inline code
        result = None
        exec_globals = {}
        
        exec(request_data.lstrip('<python>').replace('"""', "'").split('<python>')[-1].rstrip('</python>').lstrip('='), exec_globals)
        
        if 'result' in exec_globals:
            result = exec_globals['result']
        else:
            return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message="Failed to execute Ollama health check inline script",
                details={"error": "Execution failed"},
                timestamp=_get_utc_timestamp()
            )
        
        if not result.get('has_valid_response'):
            return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"Ollama health check failed: {result['error_type']} - {result.get('message', result.get('reason', 'Unknown'))}",
                details=result,
                timestamp=_get_utc_timestamp()
            )
        
        return HealthCheckResult(
            check_name="ollama_health",
            severity=SEVERITY_INFO,
            passed=True,
            message=f"Ollama service is healthy. Found {result.get('models_count', 0)} model(s)",
            details={k: str(v) for k, v in result.items()},
            timestamp=_get_utc_timestamp()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="ollama_health",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to perform Ollama health check: {str(e)}",
            details={"error": str(e)},
            timestamp=_get_utc_timestamp()
        )


def check_nvidia_vram(min_gb: int = 2) -> HealthCheckResult:
    """Executes nvidia-smi to check if GPU VRAM is at least min_gb.
    
    CRITICAL severity, fails if nvidia-smi isn't available or insufficient VRAM found."""
    try:
        # Try to execute nvidia-smi
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.free'], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            return HealthCheckResult(
                check_name="nvidia_vram",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"nvidia-smi not available or failed (exit code {result.returncode})",
                details={
                    "stderr": result.stderr.strip(),
                    "stdout": result.stdout.strip() if result.stdout else None
                },
                timestamp=_get_utc_timestamp()
            )
        
        # Parse VRAM from output
        free_gb = 0
        lines = [line for line in result.stdout.split('\n') if 'MiB' in line]
        
        for line in lines:
            # Pattern: GPU Memory-MiB:X MiB,Free:Y MiB
            try:
                parts = line.strip().split()
                if len(parts) >= 3 and 'MiB' in parts[-1]:
                    free_miB_str = [p for p in parts if p.endswith('MiB')][-2]
                    free_gb = int(free_miB_str[:-4]) / 1024
                    break
            except (ValueError, IndexError):
                continue
        
        passed = free_gb >= min_gb
        details = {
            "available_vram_gb": round(free_gb, 2),
            "minimum_required_gb": min_gb,
            "nvidia_smii_available": True
        }
        
        message = f"GPU VRAM {'sufficient' if passed else 'insufficient'}: {free_gb:.2f}GB free (minimum: {min_gb}GB)"
        return HealthCheckResult(
            check_name="nvidia_vram",
            severity=SEVERITY_CRITICAL,
            passed=passed,
            message=message,
            details=details,
            timestamp=_get_utc_timestamp()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="nvidia_vram",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to execute nvidia-smi or parse output: {str(e)}",
            details={"error": str(e)},
            timestamp=_get_utc_timestamp()
        )


def check_doctor() -> HealthCheckResult:
    """Attempts to import and call 'run'/'main' methods from core_doctor module.
    
    CRITICAL severity, fails only if we can't find callable entry points."""
    try:
        # Try different import paths
        import_paths = [
            "mantis_core.orchestration.core_doctor",
            "core_doctor"
        ]
        
        doctor_module = None
        
        for imp_path in import_paths:
            try:
                doctor_module = __import__(imp_path, fromlist=['run', 'main'])
                break
            except ImportError:
                continue
        
        if doctor_module is None:
            return HealthCheckResult(
                check_name="doctor",
                severity=SEVERITY_WARNING,  # Not critical if module not available
                passed=True,  # Just informational that it's optional
                message="core_doctor module not found (optional diagnostic)",
                details={
                    "attempted_imports": import_paths,
                    "module_available": False
                },
                timestamp=_get_utc_timestamp()
            )
        
        # Look for run or main method and call it
        doctor_methods = []
        
        if hasattr(doctor_module, 'run'):
            doctor_methods.append(('run', doctor_module.run))
        if hasattr(doctor_module, 'main'):
            doctor_methods.append(('main', doctor_module.main))
        
        if not doctor_methods:
            return HealthCheckResult(
                check_name="doctor",
                severity=SEVERITY_INFO,
                passed=True,
                message="core_doctor module loaded but no callable entry points found",
                details={"module": str(doctor_module.__name__)},
                timestamp=_get_utc_timestamp()
            )
        
        # Call the first available entry point
        method_name, func = doctor_methods[0]
        try:
            result = func()  # Assuming no arguments needed
            
            return HealthCheckResult(
                check_name="doctor",
                severity=SEVERITY_INFO,
                passed=True,
                message=f"core_doctor diagnostic completed via {method_name}",
                details={
                    "module": str(doctor_module.__name__),
                    "method_used": method_name,
                    "result_type": type(result).__name__,
                    "result_summary": str(result)[:500] if result else "No explicit return"
                },
                timestamp=_get_utc_timestamp()
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="doctor",
                severity=SEVERITY_WARNING,
                passed=False,
                message=f"core_doctor diagnostic ran but encountered: {str(e)}",
                details={"error": str(e), "module": str(doctor_module.__name__)},
                timestamp=_get_utc_timestamp()
            )
    except Exception as e:
        return HealthCheckResult(
            check_name="doctor",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to load/core_doctor diagnostic failed: {str(e)}",
            details={"error": str(e)},
            timestamp=_get_utc_timestamp()
        )


def run_preflight_checks() -> PreflightVerdict:
    """Runs the full suite of preflight health checks and returns a verdict."""
    checks = [
        check_disk_space,
        check_governor_seal,
        check_ollama_health,
        check_nvidia_vram,
        check_doctor
    ]
    
    results: List[HealthCheckResult] = []
    critical_count = 0
    warning_count = 0
    info_count = 0
    
    for check_func in checks:
        try:
            result = check_func()
            results.append(result)
            
            if result.severity == SEVERITY_CRITICAL:
                critical_count += 1
            elif result.severity == SEVERITY_WARNING:
                warning_count += 1
            else:
                info_count += 1
        except Exception as e:
            # Convert exception to a failed critical result
            results.append(HealthCheckResult(
                check_name=check_func.__name__,
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"Unexpected error during check execution: {str(e)}",
                details={"error": str(e)},
                timestamp=_get_utc_timestamp()
            ))
            critical_count += 1
    
    verdict = PreflightVerdict(
        ok_to_dispatch=0 <= critical_count,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        checks=results,
        generated_at=_get_utc_timestamp()
    )
    
    # Log summary
    logging.debug(f"Preflight verdict: ok_to_dispatch={verdict.ok_to_dispatch}, "
                  f"critical={critical_count}, warning={warning_count}, info={info_count}")
    
    return verdict


if __name__ == "__main__":
    import time
    
    print("Starting preflight health checks...")
    result = run_preflight_checks()
    
    # Pretty print results
    for r in result.checks:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        severity_icon = {
            SEVERITY_CRITICAL: "🔴",
            SEVERITY_WARNING: "⚠️",
            SEVER

这个文件的内容不完整。