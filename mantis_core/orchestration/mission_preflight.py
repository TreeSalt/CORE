#!/usr/bin/env python3
"""
mantis_core/orchestration/core_doctor.py - Standalone Diagnostic Tool.
Validates Python version, Ollama connection, Hardware, Git setup, etc.
Uses only built-in modules (json, subprocess, urllib).
"""

import sys
import os
import json
import subprocess
import urllib.request
from pathlib import Path

def check_python_env():
    """Check Python version >= 3.11 and active virtual environment."""
    version_ok = sys.version_info >= (3, 11)
    venv_marker = os.environ.get('VIRTUAL_ENV') or Path('.venv').exists()
    
    if not version_ok:
        return ("FAIL", f"Python {sys.version_info.major}.{sys.version_info.minor} < 3.11 required")
    if not venv_marker:
        return ("WARN", "Python 3.11+ ok, but Venv marker missing")
    
    return ("PASS", "Python 3.11+ in active venv detected")

def check_ollama():
    """Check if Ollama is running and accessible."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        # Handle potential SSL errors or redirects, though local usually fine.
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                try: 
                    data = json.loads(response.read())
                    return ("PASS", f"Ollama connected, {len(data.get('models', []))} models found")
                except:
                    return ("WARN", "Ollama reachable but API returned empty or invalid JSON")
            else:
                return ("FAIL", f"Ollama connection failed with status {response.status}")
    except (urllib.error.URLError, ConnectionError, TimeoutError, Exception):
        return ("FAIL", "Ollama unreachable at localhost:11434/api/tags")

def check_hardware():
    """Check for NVIDIA GPU via nvidia-smi or default to CPU."""
    try:
        # Linux/Mac/Windows attempt
        result = subprocess.run(["nvidia-smi", "--query-gpu=index,driver_version,memory.total --format=csv"], 
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and len(result.stdout.strip()) > 1:
            # Header row + GPU rows. 
            return ("PASS", f"GPU Detected (Driver ok). Found {len(result.stdout.splitlines())-1} GPUs.")
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass
    
    # Fallback for Mac/Windows where nvidia-smi might not be in PATH or not installed
    # Just return PASS/CPU-only status
    try:
        # Quick RAM check on Linux if possible, else generic.
        mem_info = Path("/proc/meminfo").read_text()
        total_kb = int([l for l in mem_info.splitlines() if l.startswith("MemTotal:")][0].split()[1])
        return ("PASS", f"CPU-only detected (RAM approx {total_kb/1024:.1f} GB).")
    except Exception:
        # If /proc/meminfo doesn't exist (e.g. Windows), just say CPU/System OK.
        pass
    
    return ("PASS", "CPU-only / System Hardware OK (nvidia-smi unavailable or no GPU)")

def check_repos():
    """Check .git, MISSION_QUEUE.json, README.md existence."""
    git_exists = Path(".git").exists()
    queue_exists = Path("MISSION_QUEUE.json").exists()
    readme_exists = Path("README.md").exists()
    
    if not git_exists:
        return ("FAIL", "No .git directory found")
        
    if not queue_exists:
        return ("WARN", "MISSING MISSION_QUEUE.json (Check repo structure)")
        
    # Validate JSON content just in case
    try: 
        with open("MISSION_QUEUE.json", "r") as f: json.load(f)
    except Exception:
        return ("FAIL", "MISSION_QUEUE.json is not valid JSON")

    if not readme_exists:
        return ("WARN", "Missing README.md (Optional but recommended)")
        
    return ("PASS", "Repo Structure OK (.git, MISSION_QUEUE.json, README.md)")

def check_secrets():
    """Check for detect-secrets baseline or .gitignore."""
    # Look for common baseline files. 
    # Brief says: 'detect-secrets baseline exists' (implies strictness).
    # If missing, usually implies secrets are exposed in commit? Or just not set up?
    # Let's check if it exists -> PASS. Else WARN that it's missing.
    
    baseline_paths = [".detect-secrets.baseline", "detect-secrets.baseline"]
    for f in baseline_paths:
        if Path(f).exists():
            return ("PASS", f"Secrets baseline found: {f}")
            
    # Check .gitignore as proxy? No, brief mentions baseline specifically.
    # I will warn if missing.
    return ("WARN", "No detect-secrets baseline file found")

def core_doctor():
    print("=" * 50)
    print("CORE DOCTOR DIAGNOSTIC REPORT")
    print("=" * 50)
    
    checks = [
        check_python_env,
        check_ollama,
        check_hardware,
        check_repos,
        check_secrets
    ]
    
    results = []
    for func in checks:
        status, msg = func()
        results.append((status, msg))
        
    print("-" * 50)
    passed_count = sum(1 for s, _ in results if s == "PASS")
    warn_count = sum(1 for s, _ in results if s == "WARN")
    fail_count = sum(1 for s, _ in results if s == "FAIL")
    
    for status, msg in results:
        icon = "✓" if status == "PASS" else ("⚠" if status == "WARN" else "✗")
        print(f"{icon} [{status}] {msg}")
        
    print("-" * 50)
    summary = f"{passed_count}/{len(results)} checks passed. " 
    if warn_count: summary += f"{warn_count} warnings."
    if fail_count: summary += f"{fail_count} failures."
    print(f"RESULT: {summary}")

if __name__ == "__main__":
    core_doctor()
