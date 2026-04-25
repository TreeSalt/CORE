---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the complete implementation of the function and its helper checks.

```python
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from typing import List

@dataclass
class PreflightCheckResult:
    name: str
    passed: bool
    message: str = ""

def check_disk_space(path: str = "/", threshold_gb: int = 10) -> PreflightCheckResult:
    """Check if sufficient disk space is available."""
    try:
        stat = os.statvfs(path)
        free_bytes = stat.f_bavail * stat.f_frsize
        free_gb = free_bytes / (1024 ** 3)
        
        if free_gb >= threshold_gb:
            return PreflightCheckResult(name="disk_space", passed=True, message=f"{free_gb:.2f} GB available")
        else:
            return PreflightCheckResult(name="disk_space", passed=False, message=f"Only {free_gb:.2f} GB available (threshold: {threshold_gb})")
    except Exception as e:
        return PreflightCheckResult(name="disk_space", passed=False, message=str(e))

def check_governor_seal(governor_path: str = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") -> PreflightCheckResult:
    """Ensure CPU governor is set to a high-performance state."""
    try:
        with open(governor_path, 'r') as f:
            governor = f.read().strip()
        
        # Allowed governors for high throughput (typically performance or schedutil)
        allowed_governors = {"performance", "schedutil"}
        
        if governor in allowed_governors or not governor:
             return PreflightCheckResult(name="governor_seal", passed=True, message=f"Governor is {governor}")
        else:
            # If it's 'powersave' or other restrictive mode
            return PreflightCheckResult(name="governor_seal", passed=False, message=f"Restricted to {governor} (requires performance/schedutil)")
    except FileNotFoundError:
        return PreflightCheckResult(name="governor_seal", passed=False, message="Sysfs governor path not found (CPU scaling disabled?)")

def check_ollama_health(host: str = "localhost", port: int = 11434) -> PreflightCheckResult:
    """Check Ollama server availability and health."""
    try:
        # Try curl first (often faster if available)
        result = subprocess.run(["curl", "-s", f"http://{host}:{port}/"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return PreflightCheckResult(name="ollama_health", passed=True, message="Ollama API is responding")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    try:
        # Fallback to raw HTTP request
        with urllib.request.urlopen(f"http://{host}:{port}", timeout=5) as response:
             return PreflightCheckResult(name="ollama_health", passed=True, message=f"Ollama API is responding (status {response.status})")
    except Exception as e:
         return PreflightCheckResult(name="ollama_health", passed=False, message=str(e))

def check_system_dependencies(host: str = "localhost", port: int = 11434) -> List[PreflightCheckResult]:
    """Run all pre-flight checks and return results."""
    results = []

    # 1. Disk Space
    results.append(check_disk_space())
    
    # 2. Governor Seal (Performance Mode)
    results.append(check_governor_seal())
    
    # 3. Ollama Health Check
    results.append(check_ollama_health(host, port))
    
    return results

# Example usage:
if __name__ == "__main__":
    checks = check_system_dependencies()
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.message}")
```

### Explanation of Changes
1.  **`PreflightCheckResult`**: A simple dataclass to encapsulate the result of a single check, making it serializable and easy to inspect.
2.  **`check_disk_space`**: Calculates free disk space on the root directory (`/`) and ensures it meets the minimum threshold (default 10GB). It catches OS-related exceptions gracefully.
3.  **`check_governor_seal`**: Reads `/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`. It validates that the governor is set to either `performance` or `schedutil`. If the system is restricted to a low-power mode like `powersave`, it marks the check as failed.
4.  **`check_ollama_health`**: Attempts to ping the Ollama API using `curl`. If `curl` isn't available, it falls back to the standard library's `urllib.request`. It returns `passed=True` if a response is received within the timeout, otherwise it returns `False` with details.
5.  **`check_system_dependencies`**: Aggregates the results of all three checks and returns them as a list, which can be printed or returned to a higher-level application.

### Usage Note
Ensure that you have `curl` installed on the host machine (common in Linux). If not, the fallback `urllib` will handle it automatically. The governor check requires writing permissions for `root` and the target CPU file must exist.