#!/usr/bin/env python3
"""
ollama_health_gate.py — CORE Infrastructure Health Gate (v2)
============================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection

v2 PATCH: Tier-aware VRAM reclamation.
  When a mission requires a smaller tier than what's currently loaded,
  unload the larger models BEFORE attempting dispatch. This solves the
  HTTP 500 cascade observed on 2026-04-17 where qwen3.5:27b was loaded
  but the daemon needed qwen3.5:4b/9b for sprinter/cruiser missions.

PRINCIPLE
'Algorithms for the deterministic, LLMs for the creative.'
VRAM accounting is deterministic. Reclamation should be deterministic.
The model fitting on the GPU is not a creative decision.

CONSTITUTIONAL BINDING
FAIL-CLOSED. If recovery fails, mission is deferred.
"""
import json
import logging
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

log = logging.getLogger("health_gate")

OLLAMA_URL = "http://localhost:11434"
VRAM_BUDGET_MB = 7500  # Leave ~500MB headroom on 8GB card
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_WAIT_SECONDS = 10
VRAM_HEADROOM_MB = 500  # Required free VRAM beyond the model size

# Repo paths for DOMAINS.yaml lookup
REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAINS_REGISTRY = REPO_ROOT / "04_GOVERNANCE" / "DOMAINS.yaml"


# ─── BASIC HEALTH CHECKS ─────────────────────────────────────

def check_ollama_alive() -> bool:
    """Ping Ollama API. Returns True if responsive."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return "models" in data
    except Exception:
        return False


def get_loaded_models() -> list[dict]:
    """Get currently loaded model entries with size info from /api/ps."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/ps", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("models", [])
    except Exception:
        return []


def get_loaded_model_names() -> list[str]:
    """Backwards-compatible: return just the names of loaded models."""
    return [m.get("name", "") for m in get_loaded_models()]


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


# ─── MODEL SIZE INTROSPECTION ────────────────────────────────

def get_model_size_mb(model_name: str) -> int:
    """Query Ollama for the on-disk size of a model in MB. Returns 0 if unknown."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for m in data.get("models", []):
                if m.get("name") == model_name:
                    return int(m.get("size", 0)) // (1024 * 1024)
    except Exception as e:
        log.warning(f"Could not query size for {model_name}: {e}")
    return 0


def classify_tier_by_size_mb(size_mb: int) -> str:
    """Classify a model by its on-disk size into sprinter/cruiser/heavy.
    
    Thresholds tuned for qwen3.5 family but generalize to any model:
      < 6 GB  -> sprinter (4B class)
      < 15 GB -> cruiser  (9B class)
      otherwise -> heavy   (27B+ class)
    """
    if size_mb < 6_000:
        return "sprinter"
    elif size_mb < 15_000:
        return "cruiser"
    return "heavy"


_TIER_RANK = {"sprinter": 0, "cruiser": 1, "heavy": 2}


def tier_is_larger_than_required(loaded_tier: str, required_tier: str) -> bool:
    """True if loaded_tier ranks higher than required_tier."""
    return _TIER_RANK.get(loaded_tier, 0) > _TIER_RANK.get(required_tier, 0)


# ─── DOMAINS.YAML LOOKUP ─────────────────────────────────────

def get_required_model_for_mission(mission: dict) -> Optional[str]:
    """Look up the model a mission's domain requires based on its primary_tier.
    
    Returns the model name (e.g., 'qwen3.5:9b') or None if not resolvable.
    Pure stdlib — does not import yaml; does a minimal parse.
    """
    if not mission:
        return None
    domain_id = mission.get("domain", "")
    if not domain_id or not DOMAINS_REGISTRY.exists():
        return None

    try:
        text = DOMAINS_REGISTRY.read_text()
    except Exception:
        return None

    # Minimal YAML walker: find the domain block, extract primary_tier and the
    # corresponding {tier}_model key. We avoid importing yaml so the health
    # gate stays pure-stdlib.
    in_target = False
    primary_tier = None
    tier_models: dict[str, str] = {}

    for line in text.split("\n"):
        stripped = line.lstrip()

        if stripped.startswith("- id:"):
            if in_target and primary_tier and tier_models.get(primary_tier):
                # Done — we already collected what we need from the prior block
                return tier_models[primary_tier]
            current_id = stripped.split(":", 1)[1].strip()
            in_target = (current_id == domain_id)
            if in_target:
                primary_tier = None
                tier_models = {}
            continue

        if not in_target:
            continue

        if stripped.startswith("primary_tier:"):
            primary_tier = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("sprinter_model:"):
            tier_models["sprinter"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("cruiser_model:"):
            tier_models["cruiser"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("heavy_model:"):
            tier_models["heavy"] = stripped.split(":", 1)[1].strip()

    # Last block in file
    if in_target and primary_tier and tier_models.get(primary_tier):
        return tier_models[primary_tier]
    return None


# ─── UNLOAD OPERATIONS ───────────────────────────────────────

def unload_model(model_name: str) -> bool:
    """Unload a single model via `ollama stop`. Returns True if successful."""
    try:
        log.info(f"  Unloading model: {model_name}")
        result = subprocess.run(
            ["ollama", "stop", model_name],
            capture_output=True, timeout=30, text=True
        )
        return result.returncode == 0
    except Exception as e:
        log.warning(f"  Failed to unload {model_name}: {e}")
        return False


def unload_all_models() -> bool:
    """Unload every currently-loaded model. Returns True if VRAM is clean."""
    for name in get_loaded_model_names():
        unload_model(name)
    time.sleep(3)
    return len(get_loaded_model_names()) == 0


def unload_models_larger_than_tier(required_tier: str) -> list[str]:
    """Unload every loaded model whose tier rank exceeds required_tier.
    Returns the list of unloaded model names.
    """
    unloaded = []
    for entry in get_loaded_models():
        name = entry.get("name", "")
        if not name:
            continue
        size_mb = get_model_size_mb(name)
        loaded_tier = classify_tier_by_size_mb(size_mb)
        if tier_is_larger_than_required(loaded_tier, required_tier):
            log.info(
                f"  TIER RECLAIM: {name} ({loaded_tier}, {size_mb}MB) "
                f"exceeds required {required_tier} — unloading"
            )
            if unload_model(name):
                unloaded.append(name)
    if unloaded:
        time.sleep(3)
    return unloaded


def restart_ollama() -> bool:
    """Attempt to restart Ollama service."""
    log.warning("  Attempting Ollama restart...")
    try:
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
        subprocess.run(["pkill", "-f", "ollama serve"],
                       capture_output=True, timeout=10)
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


# ─── PUBLIC API ──────────────────────────────────────────────

def pre_mission_health_check(mission: Optional[dict] = None) -> dict:
    """Run full health check before a mission. Tier-aware when mission given.

    Recovery sequence:
      1. Ollama alive? If not, restart up to MAX_RECOVERY_ATTEMPTS.
      2. If mission provided: look up required tier/model, unload larger models.
      3. If VRAM still under threshold after step 2, unload everything.
      4. Final alive check; report healthy iff Ollama responds.

    Returns:
      {
        "healthy": bool,
        "action_taken": str,
        "vram": {"total": int, "used": int, "free": int},
        "tier_reclaimed": list[str],   # models unloaded for tier mismatch
        "required_model": str | None,  # model the mission needs
        "required_tier": str | None,
      }
    """
    report = {
        "healthy": False,
        "action_taken": "none",
        "vram": {},
        "tier_reclaimed": [],
        "required_model": None,
        "required_tier": None,
    }

    # Step 1: Ollama alive?
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

    # Step 2: Tier-aware reclamation (only if we know what mission needs)
    required_model = get_required_model_for_mission(mission)
    if required_model:
        report["required_model"] = required_model
        required_size_mb = get_model_size_mb(required_model)
        required_tier = classify_tier_by_size_mb(required_size_mb)
        report["required_tier"] = required_tier

        log.info(
            f"HEALTH GATE: mission requires {required_model} "
            f"(tier={required_tier}, size={required_size_mb}MB)"
        )

        unloaded = unload_models_larger_than_tier(required_tier)
        if unloaded:
            report["tier_reclaimed"] = unloaded
            report["action_taken"] = f"tier_reclaim_{len(unloaded)}_models"
            log.info(f"  ✅ Reclaimed VRAM by unloading: {unloaded}")

        # Check whether required model now fits with headroom
        vram = get_vram_usage_mb()
        if required_size_mb > 0 and vram["free"] < (required_size_mb + VRAM_HEADROOM_MB):
            log.warning(
                f"HEALTH GATE: VRAM still tight after tier reclaim "
                f"(free={vram['free']}MB, need={required_size_mb + VRAM_HEADROOM_MB}MB) "
                f"— unloading remaining models"
            )
            unload_all_models()
            report["action_taken"] += "_then_full_unload"

    # Step 3: VRAM threshold check (legacy fallback for missions without context)
    vram = get_vram_usage_mb()
    report["vram"] = vram

    if (not required_model) and vram["total"] > 0 and vram["free"] < 1000:
        log.warning(
            f"HEALTH GATE: VRAM low ({vram['free']}MB free / {vram['total']}MB total)"
        )
        unload_all_models()
        vram = get_vram_usage_mb()
        report["vram"] = vram
        if report["action_taken"] == "none":
            report["action_taken"] = "vram_cleared"

    # Step 4: Final alive check
    if check_ollama_alive():
        report["healthy"] = True
        log.info(
            f"HEALTH GATE: ✅ Ollama healthy | VRAM: {vram.get('free', '?')}MB free"
        )
    else:
        log.critical("HEALTH GATE: ❌ Ollama dead after recovery")
        report["action_taken"] += "_then_final_check_failed"

    return report


def ensure_clean_vram() -> dict:
    """Detect and clear CPU/GPU split mode by unloading all models.
    Returns {"clean": bool, "had_split": bool, "unloaded": list[str]}.
    """
    loaded = get_loaded_model_names()
    if not loaded:
        return {"clean": True, "had_split": False, "unloaded": []}

    # Heuristic: if any loaded model is larger than VRAM_BUDGET_MB, assume split
    had_split = False
    for name in loaded:
        size_mb = get_model_size_mb(name)
        if size_mb > VRAM_BUDGET_MB:
            had_split = True
            break

    if had_split:
        log.warning(f"VRAM COOLDOWN: detected potential split-mode models {loaded}")
        unload_all_models()
        return {
            "clean": len(get_loaded_model_names()) == 0,
            "had_split": True,
            "unloaded": loaded,
        }

    return {"clean": True, "had_split": False, "unloaded": []}


def get_model_load_mode() -> list[dict]:
    """Check ollama ps for CPU/GPU split mode. Returns list of loaded model info."""
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            capture_output=True, text=True, timeout=10
        )
        models = []
        for line in result.stdout.split("\n")[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    models.append({"name": parts[0], "raw": line})
        return models
    except Exception:
        return []


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    # Standalone test: simulate a mission requiring sprinter
    test_mission = {"domain": "06_BENCHMARKING", "id": "smoke_test"}
    print("─── Standalone test: requesting sprinter for 06_BENCHMARKING ───")
    result = pre_mission_health_check(test_mission)
    print(json.dumps(result, indent=2))
