"""core_sdk.health — Ollama and VRAM health monitoring."""
from __future__ import annotations
import json
import subprocess
import re
from typing import List, Optional
from .types import HealthStatus

def check_ollama_alive(base_url: str = "http://localhost:11434") -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False

def get_loaded_models(base_url: str = "http://localhost:11434") -> List[str]:
    try:
        import urllib.request
        req = urllib.request.Request(f"{base_url}/api/ps")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []

def get_vram_status() -> HealthStatus:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            parts = out.stdout.strip().split(",")
            if len(parts) >= 3:
                return HealthStatus(
                    healthy=True,
                    vram_total=int(parts[0].strip()),
                    vram_used=int(parts[1].strip()),
                    vram_free=int(parts[2].strip()),
                    models_loaded=get_loaded_models(),
                )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return HealthStatus(healthy=False, vram_total=0, vram_used=0, vram_free=0, models_loaded=[])

def unload_model(model_name: str) -> bool:
    try:
        r = subprocess.run(["ollama", "stop", model_name], capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False

def ensure_healthy(min_free_mb: int = 2000) -> HealthStatus:
    status = get_vram_status()
    if status.vram_free < min_free_mb and status.models_loaded:
        for m in status.models_loaded:
            unload_model(m)
        status = get_vram_status()
    return status
