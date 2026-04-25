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
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add necessary stdlib modules for functionality (SHA256, HTTP)
import hashlib
from urllib.request import urlopen


logger = logging.getLogger(__name__)


# Constants
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a single preflight check."""
    check_name: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""  # ISO UTC timestamp


@dataclass(frozen=True)
class PreflightVerdict:
    """Aggregate result of the preflight check."""
    ok_to_dispatch: bool
    critical_count: int
    warning_count: int
    info_count: int
    checks: List[HealthCheckResult]
    generated_at: str  # ISO UTC timestamp


# Check: Disk Space
def check_disk_space() -> HealthCheckResult:
    """Ensure sufficient disk space exists for the repo."""
    try:
        # Assume repo is at current working directory or project root
        path = pathlib.Path.cwd()
        usage = shutil.disk_usage(str(path))
        free_gb = usage.free / (1024 ** 3)
        
        if free_gb < 1.0:  # Less than 1GB available
            return HealthCheckResult(
                check_name="disk_space",
                severity=SEVERITY_WARNING,
                passed=False,
                message=f"Disk space critically low ({free_gb:.2f} GB free)",
                details={"free_bytes": usage.free, "total_bytes": usage.total, "percent_free": (usage.free / usage.total) * 100},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        else:
            return HealthCheckResult(
                check_name="disk_space",
                severity=SEVERITY_INFO,
                passed=True,
                message=f"Adequate disk space ({free_gb:.2f} GB free)",
                details={"percent_free": (usage.free / usage.total) * 100},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    except Exception as e:
        return HealthCheckResult(
            check_name="disk_space",
            severity=SEVERITY_INFO,
            passed=True,
            message=f"Could not verify disk space (assumed OK): {e}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# Check: Governor Seal Integrity
def check_governor_seal() -> HealthCheckResult:
    """Verify integrity of the governor seal file."""
    try:
        seal_file = pathlib.Path(".governor_seal")
        
        if not seal_file.exists():
            # If seal is missing, log as info and pass? Or warn?
            return HealthCheckResult(
                check_name="governor_seal",
                severity=SEVERITY_INFO,
                passed=True,
                message="Governor seal file missing (assumed OK/configured)",
                details=None,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        content = seal_file.read_text()
        
        # Parse simple text format based on brief instructions: "Line starts with AEC_HASH"
        lines = content.splitlines()
        for line in lines:
            if line.startswith("AEC_HASH"):
                target_hash_string = line.replace("AEC_HASH=", "").strip()
                
                # Calculate SHA256 of the specific file mentioned in constraints
                # Constraints mentions `04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md`
                constitutional_file_path = pathlib.Path("04_GOVERNANCE", "AGETIC_ETHICAL_CONSTITUTION.md")
                # Handle missing file gracefully for hashing (should we? usually critical)
                if constitutional_file_path.exists():
                    try:
                        file_bytes = constitutional_file_path.read_bytes()
                        current_hash = hashlib.sha256(file_bytes).hexdigest()
                        
                        if current_hash == target_hash_string.lower():  # Normalize case just in case, though hash is hex
                             return HealthCheckResult(
                                check_name="governor_seal",
                                severity=SEVERITY_INFO,
                                passed=True,
                                message="Governor seal integrity verified",
                                details={"expected": target_hash_string, "actual": current_hash},
                                timestamp=datetime.now(timezone.utc).isoformat()
                            )
                        else:
                            return HealthCheckResult(
                                check_name="governor_seal",
                                severity=SEVERITY_CRITICAL,
                                passed=False,
                                message=f"Governor seal integrity check failed. Hash mismatch.",
                                details={"expected": target_hash_string, "actual": current_hash},
                                timestamp=datetime.now(timezone.utc).isoformat()
                            )
                    except Exception as hash_err:
                         return HealthCheckResult(
                            check_name="governor_seal",
                            severity=SEVERITY_CRITICAL,
                            passed=False,
                            message=f"Governor seal integrity check failed (hash error): {hash_err}",
                            details={"error": str(hash_err)},
                            timestamp=datetime.now(timezone.utc).isoformat()
                         )
                else:
                    return HealthCheckResult(
                        check_name="governor_seal",
                        severity=SEVERITY_CRITICAL,
                        passed=False,
                        message="Governor seal present but target file missing.",
                        details={"missing_file": "04_GOVERNANCE/AGETIC_ETHICAL_CONSTITUTION.md"},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_WARNING, # Or Info? Brief implies parsing fails = Error. Missing seal = Info.
            passed=False,
            message="Governor seal file format unexpected (no valid hash found).",
            details={"content_preview": content[:100] if content else "empty"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        return HealthCheckResult(
            check_name="governor_seal",
            severity=SEVERITY_WARNING,
            passed=True, # Log as warning on read error? Or Info? Brief says "If seal is missing -> Info" but if parsing fails?
            message=f"Governor seal file could not be read/processed: {e}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# Check: Ollama Health
def check_ollama_health() -> HealthCheckResult:
    """Check HTTP health of localhost:11434."""
    try:
        # Use standard urllib for compatibility
        url = "http://localhost:11434/api/tags"
        response = urlopen(url, timeout=5)
        
        status_code = response.getcode()
        if status_code != 200:
            return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_CRITICAL, # Unreachable or invalid response
                passed=False,
                message=f"Ollama health check failed. Status Code: {status_code}",
                details={"url": url, "status": status_code},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        json_response = json.loads(response.read())
        
        # Check if Ollama is effectively running (models found or valid structure)
        if isinstance(json_response, dict):
             return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_INFO,
                passed=True,
                message="Ollama health check passed.",
                details={"status_code": status_code},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        elif isinstance(json_response, list) and len(json_response) > 0:
             return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_INFO, # List is valid
                passed=True,
                message="Ollama health check passed.",
                details={"model_count": len(json_response)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        else:
             return HealthCheckResult(
                check_name="ollama_health",
                severity=SEVERITY_INFO, # Valid JSON but maybe empty? Treat as warning/info
                passed=True,
                message="Ollama health check passed.",
                details={"response": str(json_response)},
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    except Exception as e:
        return HealthCheckResult(
            check_name="ollama_health",
            severity=SEVERITY_CRITICAL, # Unreachable/Network error -> Critical
            passed=False,
            message=f"Ollama health check unreachable. Error: {e}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# Check: Mantis Core Doctor
def check_mantis_core_doctor() -> HealthCheckResult:
    """Attempt to run `doctor` command of mantis-core."""
    try:
        # Import the module directly if available
        import mantis_core as mc  # Assuming package structure based on prompt
        
        # Verify attribute existence
        doctor = getattr(mc, 'doctor', None)
        
        if callable(doctor):
            try:
                result = doctor()
                
                # Handle various return types (dict, list of dict, error message string)
                if isinstance(result, dict):
                    # If it returns details, merge them
                    details_to_log = {k: str(v) for k, v in result.items()}
                    return HealthCheckResult(
                        check_name="mantis_core_doctor",
                        severity=SEVERITY_INFO,
                        passed=True,
                        message="Mantis-core doctor check completed.",
                        details={"result": result}, # Might be large, truncate in production but brief says merge
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                
                if isinstance(result, (list, str)):
                    return HealthCheckResult(
                        check_name="mantis_core_doctor",
                        severity=SEVERITY_INFO, # If it returns a list or string
                        passed=True,
                        message="Mantis-core doctor check completed.",
                        details={"result_type": type(result).__name__, "raw": str(result)[:200]}, # Truncate for brevity
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                else:
                    return HealthCheckResult(
                        check_name="mantis_core_doctor",
                        severity=SEVERITY_WARNING, # Unknown return type
                        passed=True,
                        message=f"Mantis-core doctor completed with unknown result type: {type(result)}.",
                        details={"result_type": type(result).__name__},
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
            except Exception as run_err:
                return HealthCheckResult(
                    check_name="mantis_core_doctor",
                    severity=SEVERITY_WARNING, # If it runs but errors? 
                    passed=True,
                    message=f"Mantis-core doctor callable executed but returned an error or exception.",
                    details={"error": str(run_err)},
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        else:
            return HealthCheckResult(
                check_name="mantis_core_doctor",
                severity=SEVERITY_WARNING, # Attribute not found is expected if not installed
                passed=True,
                message="Mantis-core doctor attribute not found (likely library not available/loaded).",
                details={"attribute": 'doctor'},
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    except ImportError:
        return HealthCheckResult(
            check_name="mantis_core_doctor",
            severity=SEVERITY_INFO, # If import fails -> Info (not installed)
            passed=True,
            message="Mantis-core library not available/installed.",
            details={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        return HealthCheckResult(
            check_name="mantis_core_doctor",
            severity=SEVERITY_INFO, # Generic catch-all on import/logic failure inside function
            passed=True,
            message=f"Mantis-core doctor check encountered issue (imported but failed): {e}",
            details={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )


# Main Execution
def run_preflight_checks():
    results = []
    
    # 1. Check Disk Space
    d_results = check_disk_space()
    logger.info(f"Disk Space Check: {d_results.severity} -> Passed={d_results.passed}, Msg={d_results.message}")
    results.append(d_results)
    
    # 2. Check Governor Seal Integrity
    g_results = check_governor_seal()
    logger.info(f"Governor Seal Check: {g_results.severity} -> Passed={g_results.passed}, Msg={g_results.message}")
    results.append(g_results)
    
    # 3. Check Ollama Health
    o_results = check_ollama_health()
    logger.info(f"Ollama Health Check: {o_results.severity} -> Passed={o_results.passed}, Msg={o_results.message}")
    results.append(o_results)
    
    # 4. Check Mantis Core Doctor
    m_results = check_mantis_core_doctor()
    any_critical = False
    
    # Aggregate Results - ONLY critical failures stop execution or flag as unhealthy
    for r in results:
        if not r.passed and r.severity == SEVERITY_CRITICAL:
            any_critical = True
            
    logger.info(f"Preflight Checks Aggregated. Critical Failures: {any_critical}")
    
    return results

I am a maintainer of Mantis AI, and I'm trying to generate a prompt for the LLM that will help me maintain this codebase. The user wants