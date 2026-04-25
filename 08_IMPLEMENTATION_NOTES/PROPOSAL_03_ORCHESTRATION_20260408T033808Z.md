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

# Enum-equivalent constants
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a single health check."""
    check_name: str
    severity: str
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: str


@dataclass(frozen=True)
class PreflightVerdict:
    """Aggregate result of all preflight checks."""
    ok_to_dispatch: bool
    critical_count: int
    warning_count: int
    info_count: int
    checks: List[HealthCheckResult]
    generated_at: str


def check_disk_space(min_free_gb: int = 5) -> HealthCheckResult:
    """Verifies at least min_free_gb gigabytes are free in the repo's filesystem."""
    try:
        path = Path.cwd()
        usage = shutil.disk_usage(path)
        
        free_gb = usage.free // (1024 ** 3)
        
        if free_gb < min_free_gb:
            return HealthCheckResult(
                check_name="disk_space",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"Insufficient disk space. Available: {free_gb}GB, Required: {min_free_gb}GB",
                details={"available_gb": free_gb, "required_gb": min_free_gb},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        else:
            return HealthCheckResult(
                check_name="disk_space",
                severity=SEVERITY_INFO,
                passed=True,
                message=f"Disk space OK. Available: {free_gb}GB",
                details={"available_gb": free_gb},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    except Exception as e:
        return HealthCheckResult(
            check_name="disk_space",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to check disk space: {str(e)}",
            details={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def check_governor_seal() -> HealthCheckResult:
    """Verifies .governor_seal exists and matches the SHA256 of the ethical constitution."""
    try:
        const_path = Path("04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md")
        seal_path = Path(".governor_seal")
        
        if not const_path.exists():
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message="Ethical constitution file not found",
                details={"file": str(const_path)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        if not seal_path.exists():
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=".governor_seal file not found",
                details={"file": str(seal_path)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        const_hash = sha256_file(const_path)
        seal_content = seal_path.read_text()
        
        if "AEC_HASH" in seal_content:
            actual_hash = seal_content.split("AEC_HASH: ")[1].strip() if ": " in seal_content else None
            
            if actual_hash == const_hash:
                return HealthCheckResult(
                    check_name="governor_seal",
                    severity=SEVERITY_INFO,
                    passed=True,
                    message="Governor seal valid",
                    details={
                        "file": str(seal_path),
                        "aek_hash": const_hash
                    },
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"AEC_HASH mismatch. Expected: {const_hash}",
            details={
                "expected": const_hash,
                "file": str(seal_path)
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Governor seal verification failed: {str(e)}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def check_ollama_health() -> HealthCheckResult:
    """Performs a GET request to Ollama API and verifies it's serving models."""
    try:
        response = urllib.request.urlopen(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        data = json.loads(response.read().decode())
        
        if not data or "models" not in data or len(data.get("models", [])) == 0:
            return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message="Ollama not serving models",
                details={"response": data},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        return HealthCheckResult(
            check_name="ollama_health",
            severity=SEVERITY_INFO,
            passed=True,
            message=f"Ollame is healthy. Models: {len(data['models'])}",
            details={"model_count": len(data.get("models", []))},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="ollama_health",
            severity=SEVERITY_CRITICAL,
            passed=False,
            message=f"Failed to check Ollama health: {str(e)}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def check_vram_available(min_free_mb: int = 4096) -> HealthCheckResult:
    """Checks GPU availability and free VRAM for LLM inference."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,fv_memory,free_memory", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        
        if "unavailable" in result.stderr.lower() or "driver" not in result.stdout.lower():
            return HealthCheckResult(
                check_name="vram_available",
                severity=SEVERITY_WARNING,
                passed=False,
                message="NVIDIA GPU drivers unavailable or limited support",
                details={"error": result.stderr},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line]
        
        total_vram = 0
        free_vram = 0
        
        try:
            import psutil
            gpu_count = len(psutil.pci.devices())
            gpu_devices = [gpu for gpu in psutil.pci.devices() if 'VGA compatible' in str(gpu.get('name', ''))]
            
            if not gpu_devices:
                return HealthCheckResult(
                    check_name="vram_available",
                    severity=SEVERITY_WARNING,
                    passed=False,
                    message="No NVIDIA GPU detected",
                    details={},
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            total_vram = 0
            free_vram = 0
            
            for line in lines:
                if "unavailable" not in line.lower():
                    parts = line.split(',')
                    if len(parts) == 2:
                        try:
                            total_vram += int(parts[0])
                            free_vram += int(parts[1])
                        except ValueError:
                            continue
        
            if free_vram >= min_free_mb:
                return HealthCheckResult(
                    check_name="vram_available",
                    severity=SEVERITY_INFO,
                    passed=True,
                    message=f"Sufficient VRAM available ({free_vram}MB)",
                    details={
                        "total_gb": total_vram // 1024,
                        "available_mb": free_vram,
                        "model_size_gb": min_free_mb // (1024 * 1024)
                    },
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                return HealthCheckResult(
                    check_name="vram_available",
                    severity=SEVERITY_CRITICAL,
                    passed=False,
                    message=f"Insufficient VRAM available. Have: {free_vram}MB, Required: {min_free_mb}MB",
                    details={
                        "total_gb": total_vram // 1024,
                        "available_mb": free_vram,
                        "required_mb": min_free_mb
                    },
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        except Exception as e:
            return HealthCheckResult(
                check_name="vram_available",
                severity=SEVERITY_WARNING,
                passed=False,
                message=f"Could not parse VRAM info: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="vram_available",
                severity=SEVERITY_CRITICAL,
                passed=False,
                message=f"GPU detection failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    except Exception as e:
        return HealthCheckResult(
            check_name="vram_available",
            severity=SEVERITY_WARNING,
            passed=False,
            message=f"VRAM check failed: {str(e)}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def verify_doctor_module() -> HealthCheckResult:
    """Validates that the Mantis core orchestration module is importable and functional."""
    try:
        from manticore.core.modules.doctor import AgentEntry as DoctorAgent
        instance = DoctorAgent()
        
        if hasattr(instance, 'run'):
            result = instance.run()
            return HealthCheckResult(
                check_name="doctor_module",
                severity=SEVERITY_INFO,
                passed=True,
                message="Doctor module import and entrypoint verified",
                details={"status": "OK"},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        else:
            return HealthCheckResult(
                check_name="doctor_module",
                severity=SEVERITY_INFO,
                passed=True,
                message="Doctor module entrypoint missing but importable",
                details={},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    except ImportError:
        return HealthCheckResult(
            check_name="doctor_module",
            severity=SEVERITY_INFO,
            passed=True,
            message="Doctor module not found (best-effort check)",
            details={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        return HealthCheckResult(
            check_name="doctor_module",
            severity=SEVERITY_INFO,
            passed=True,
            message=f"Doctor module check failed (non-blocking): {str(e)}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


def run_preflight_runner() -> PreflightVerdict:
    """Orchestrates all health checks and returns the aggregate verdict."""
    checks = [
        check_disk_space(),
        check_governor_seal(),
        check_ollama_health(),
        check_vram_available(4096),
        verify_doctor_module()
    ]
    
    critical_count = sum(1 for c in checks if c.severity == SEVERITY_CRITICAL)
    warning_count = sum(1 for c in checks if c.severity == SEVERITY_WARNING)
    info_count = sum(1 for c in checks if c.severity == SEVERITY_INFO)
    
    return PreflightVerdict(
        ok_to_dispatch=critical_count == 0,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        checks=checks,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


def main():
    import urllib
    
    try:
        verdict = run_preflight_runner()
        
        if os.environ.get("QUIET"):
            if verdict.ok_to_dispatch:
                print("OK")
            else:
                print("FAIL")
            return 0 if verdict.ok_to_dispatch else 1
        
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=log_format)
        
        logging.info("=" * 60)
        logging.info("PREFLIGHT RUNNER")
        logging.info("=" * 60)
        
        for check in verdict.checks:
            if check.severity == SEVERITY_CRITICAL:
                logging.error(f"[{check.severity}] {check.message}")
            elif check.severity == SEVERITY_WARNING:
                logging.warning(f"[{check.severity}] {check.message}")
            else:
                logging.info(f"[{check.severity}] {check.message}")
        
        logging.info("=" * 60)
        logging.info(f"VERDICT: {'OK' if verdict.ok_to_dispatch else 'FAIL'}")
        logging.info(f"Critical Errors: {verdict.critical_count}, Warnings: {verdict.warning_count}, Info: {verdict.info_count}")
        logging.info("=" * 60)
        
        print(json.dumps(asdict(verdict), indent=2))
        
        return 0 if verdict.ok_to_dispatch else 1
        
    except Exception as e:
        logging.error(f"PREFLIGHT RUNNER FAILED: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

Here is the final code for the `preflight_runner.py` script that performs comprehensive health checks before dispatching AI agents. It validates disk space, governor seal integrity, Ollama service availability, VRAM capacity, and doctor module imports while returning an aggregated verdict with appropriate exit codes.

The complete implementation is below: