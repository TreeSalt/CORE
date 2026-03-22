#!/usr/bin/env python3
"""
CORE RECONNECT — Cloud/Local AI Reconnection Module
====================================================
Adds `core reconnect` subcommand to core_cli.py.

Handles:
  1. Ollama restart + model reload (local inference)
  2. Cloud API connectivity check (Claude/Gemini)
  3. Reset any IN_PROGRESS missions back to PENDING
  4. VRAM cleanup via model unload before reload

Usage:
  core reconnect          # Full reconnect (Ollama + cloud + reset missions)
  core reconnect --local  # Ollama only
  core reconnect --cloud  # Cloud API check only
  core reconnect --reset  # Reset stuck missions only

Integration:
  Copy cmd_reconnect() into core_cli.py and add the subparser.
"""

import subprocess
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:9b"


def log(level, msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} [{level}] {msg}")


def check_ollama_alive():
    """Check if Ollama HTTP endpoint responds."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return True, models
    except Exception as e:
        return False, str(e)


def restart_ollama():
    """Kill and restart Ollama service."""
    log("INFO", "Stopping Ollama...")

    # Try systemctl first, fall back to pkill
    result = subprocess.run(
        ["systemctl", "is-active", "ollama"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        subprocess.run(["sudo", "systemctl", "restart", "ollama"], check=False)
    else:
        subprocess.run(["pkill", "-f", "ollama"], check=False)
        time.sleep(2)
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    log("INFO", "Waiting for Ollama to come online...")
    for i in range(15):
        time.sleep(2)
        alive, info = check_ollama_alive()
        if alive:
            log("INFO", f"Ollama is alive. Loaded models: {info}")
            return True
    log("ERROR", "Ollama did not come online after 30 seconds")
    return False


def unload_models():
    """Unload all models from VRAM to free memory before reload."""
    alive, models = check_ollama_alive()
    if not alive:
        return

    for model in models:
        log("INFO", f"Unloading model: {model}")
        try:
            payload = json.dumps({"model": model, "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=30)
        except Exception:
            pass  # Model may already be unloaded
    time.sleep(2)


def reload_model(model=DEFAULT_MODEL):
    """Force-pull and warm-load the default model into VRAM."""
    log("INFO", f"Pulling model: {model}")
    result = subprocess.run(
        ["ollama", "pull", model],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        log("ERROR", f"Failed to pull {model}: {result.stderr}")
        return False

    # Warm the model with a tiny inference to force VRAM load
    log("INFO", f"Warming model: {model}")
    try:
        payload = json.dumps({
            "model": model,
            "prompt": "ping",
            "stream": False,
            "options": {"num_predict": 1}
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            log("INFO", f"Model warm: {model} responded in {data.get('total_duration', 0) / 1e9:.1f}s")
            return True
    except Exception as e:
        log("ERROR", f"Model warm failed: {e}")
        return False


def check_cloud_apis():
    """Check cloud API connectivity (Claude, Gemini)."""
    results = {}

    # Check Claude API
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            method="GET"
        )
        urllib.request.urlopen(req, timeout=10)
        results["claude"] = "reachable"
    except urllib.error.HTTPError as e:
        # 401/405 means the endpoint is reachable, just auth-gated
        results["claude"] = f"reachable (HTTP {e.code})"
    except Exception as e:
        results["claude"] = f"UNREACHABLE: {e}"

    # Check Gemini API
    try:
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1/models",
            method="GET"
        )
        urllib.request.urlopen(req, timeout=10)
        results["gemini"] = "reachable"
    except urllib.error.HTTPError as e:
        results["gemini"] = f"reachable (HTTP {e.code})"
    except Exception as e:
        results["gemini"] = f"UNREACHABLE: {e}"

    for api, status in results.items():
        level = "INFO" if "reachable" in status else "ERROR"
        log(level, f"Cloud API [{api}]: {status}")

    return results


def reset_stuck_missions():
    """Reset any IN_PROGRESS missions back to PENDING."""
    if not QUEUE_PATH.exists():
        log("WARN", f"Queue not found: {QUEUE_PATH}")
        return 0

    queue = json.loads(QUEUE_PATH.read_text())
    reset_count = 0

    for mission in queue.get("missions", []):
        if mission.get("status") == "IN_PROGRESS":
            mission["status"] = "PENDING"
            mission["reset_reason"] = "core_reconnect"
            mission["reset_at"] = datetime.now(timezone.utc).isoformat()
            reset_count += 1

    if reset_count > 0:
        QUEUE_PATH.write_text(json.dumps(queue, indent=2))
        log("INFO", f"Reset {reset_count} stuck mission(s) from IN_PROGRESS to PENDING")
    else:
        log("INFO", "No stuck missions found")

    return reset_count


def cmd_reconnect(args):
    """
    Full reconnect sequence:
    1. Unload stale models from VRAM
    2. Restart Ollama
    3. Reload default model
    4. Check cloud APIs
    5. Reset stuck missions
    """
    do_local = args.local or (not args.cloud and not args.reset)
    do_cloud = args.cloud or (not args.local and not args.reset)
    do_reset = args.reset or (not args.local and not args.cloud)

    log("INFO", "=" * 60)
    log("INFO", "CORE RECONNECT — AI INFRASTRUCTURE RECOVERY")
    log("INFO", "=" * 60)

    success = True

    if do_local:
        log("INFO", "--- Phase 1: Local Inference (Ollama) ---")
        alive, info = check_ollama_alive()
        if alive:
            log("INFO", f"Ollama is responding. Models: {info}")
            unload_models()

        if not restart_ollama():
            log("ERROR", "Ollama restart failed")
            success = False
        else:
            if not reload_model():
                log("ERROR", "Model reload failed")
                success = False

    if do_cloud:
        log("INFO", "--- Phase 2: Cloud API Connectivity ---")
        results = check_cloud_apis()
        if any("UNREACHABLE" in v for v in results.values()):
            log("WARN", "Some cloud APIs are unreachable — check network/keys")

    if do_reset:
        log("INFO", "--- Phase 3: Mission Queue Reset ---")
        reset_stuck_missions()

    log("INFO", "=" * 60)
    if success:
        log("INFO", "RECONNECT COMPLETE — factory ready for `core run`")
    else:
        log("ERROR", "RECONNECT INCOMPLETE — check errors above")
    log("INFO", "=" * 60)

    return 0 if success else 1


# ============================================================
# INTEGRATION INSTRUCTIONS FOR core_cli.py
# ============================================================
#
# 1. Add this import at the top of core_cli.py:
#    from scripts.core_reconnect import cmd_reconnect
#
# 2. Add the subparser in main() where other subparsers are defined:
#
#    p_reconnect = subparsers.add_parser(
#        "reconnect",
#        help="Reconnect to local/cloud AI and reset stuck missions"
#    )
#    p_reconnect.add_argument("--local", action="store_true",
#                             help="Reconnect Ollama only")
#    p_reconnect.add_argument("--cloud", action="store_true",
#                             help="Check cloud APIs only")
#    p_reconnect.add_argument("--reset", action="store_true",
#                             help="Reset stuck missions only")
#    p_reconnect.set_defaults(func=cmd_reconnect)
#
# 3. Usage:
#    core reconnect          # Full reconnect
#    core reconnect --local  # Ollama restart only
#    core reconnect --cloud  # API check only
#    core reconnect --reset  # Mission reset only
# ============================================================


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CORE Reconnect")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--cloud", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    sys.exit(cmd_reconnect(args))
