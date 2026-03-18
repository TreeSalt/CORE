#!/usr/bin/env python3
"""
ollama_health_gate.py — CORE Infrastructure Health Gate
=======================================================
Pre-mission health check that ensures Ollama is alive and VRAM is clear.
Called before every mission dispatch. If unhealthy, attempts auto-recovery.

Constitutional binding: FAIL-CLOSED. If recovery fails, mission is deferred.
"""
import json
import logging
import subprocess
import time
import urllib.request
import urllib.error

log = logging.getLogger("health_gate")

OLLAMA_URL = "http://localhost:11434"
VRAM_BUDGET_MB = 7500  # Leave ~500MB headroom on 8GB card
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_WAIT_SECONDS = 10


def check_ollama_alive() -> bool:
    """Ping Ollama API. Returns True if responsive."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return "models" in data
    except Exception:
        return False


def get_loaded_models() -> list[str]:
    """Get currently loaded model names from Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/ps", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def get_vram_usage_mb() -> dict:
    """Query nvidia-smi for VRAM usage. Returns {total, used, free} in MB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            return {
                "total": int(parts[0].strip()),
                "used": int(parts[1].strip()),
                "free": int(parts[2].strip()),
            }
    except Exception:
        pass
    return {"total": 0, "used": 0, "free": 0}


def unload_all_models() -> bool:
    """Unload all models from Ollama to free VRAM."""
    models = get_loaded_models()
    for model in models:
        try:
            log.info(f"  Unloading model: {model}")
            subprocess.run(
                ["ollama", "stop", model],
                capture_output=True, timeout=30
            )
        except Exception as e:
            log.warning(f"  Failed to unload {model}: {e}")
    time.sleep(3)
    return len(get_loaded_models()) == 0


def restart_ollama() -> bool:
    """Attempt to restart Ollama service."""
    log.warning("  Attempting Ollama restart...")
    try:
        # Try systemctl first
        result = subprocess.run(
            ["systemctl", "--user", "restart", "ollama"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            time.sleep(5)
            return check_ollama_alive()
    except Exception:
        pass

    try:
        # Kill and restart manually
        subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True, timeout=10)
        time.sleep(3)
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(8)
        return check_ollama_alive()
    except Exception as e:
        log.error(f"  Ollama restart failed: {e}")
        return False


def pre_mission_health_check() -> dict:
    """
    Run full health check before a mission. Returns:
        {"healthy": bool, "action_taken": str, "vram": dict}

    Recovery sequence:
    1. Check if Ollama is alive → if not, restart
    2. Check VRAM usage → if over budget, unload models
    3. Re-check Ollama after recovery → if still dead, FAIL-CLOSED
    """
    report = {"healthy": False, "action_taken": "none", "vram": {}}

    # Step 1: Is Ollama alive?
    if not check_ollama_alive():
        log.warning("HEALTH GATE: Ollama not responding")
        report["action_taken"] = "restart_attempted"

        for attempt in range(MAX_RECOVERY_ATTEMPTS):
            log.info(f"  Recovery attempt {attempt + 1}/{MAX_RECOVERY_ATTEMPTS}")
            if restart_ollama():
                log.info("  Ollama recovered after restart")
                report["action_taken"] = f"restart_success_attempt_{attempt + 1}"
                break
            time.sleep(RECOVERY_WAIT_SECONDS)
        else:
            log.critical("HEALTH GATE: Ollama unrecoverable after all attempts")
            report["action_taken"] = "restart_failed"
            return report

    # Step 2: Check VRAM
    vram = get_vram_usage_mb()
    report["vram"] = vram

    if vram["total"] > 0 and vram["free"] < 1000:
        log.warning(f"HEALTH GATE: VRAM low ({vram['free']}MB free / {vram['total']}MB total)")
        unload_all_models()
        vram = get_vram_usage_mb()
        report["vram"] = vram
        report["action_taken"] = "vram_cleared"

    # Step 3: Final alive check
    if check_ollama_alive():
        report["healthy"] = True
        log.info(f"HEALTH GATE: ✅ Ollama healthy | VRAM: {vram.get('free', '?')}MB free")
    else:
        log.critical("HEALTH GATE: ❌ Ollama dead after recovery")
        report["action_taken"] = "final_check_failed"

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = pre_mission_health_check()
    print(json.dumps(result, indent=2))
