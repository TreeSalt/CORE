"""Dynamic timeout manager — learns from past execution times.

Never cuts off a model mid-generation. Instead, uses historical
completion times per domain+tier+memory_mode to set intelligent timeouts.

Design principles:
  - The creative models get as much time as they need
  - The system adapts to them, not the other way around
  - No hard ceiling — CORE measures, learns, adapts
  - SPLIT mode (VRAM+RAM) gets proportionally more time than VRAM-only
  - First-run estimation based on model size and memory mode
"""
import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

HISTORY_FILE = Path(__file__).resolve().parent / "timeout_history.json"

# Baseline defaults — only used when zero history exists
DEFAULT_TIMEOUT_VRAM = 900       # 15 min — 9B on GPU completes in 3-7 min
DEFAULT_TIMEOUT_SPLIT = 5400     # 90 min — 27B on VRAM+RAM at ~1-2 tok/s
HEADROOM_MULTIPLIER = 2.5        # Give 2.5x the longest observed time
MIN_TIMEOUT = 600                # 10 min absolute floor

# First-run estimation: seconds per GB of model in each memory mode
# These are conservative starting points — the system learns quickly
SECONDS_PER_GB = {
    "VRAM": 120,    # ~2 min per GB on dedicated GPU
    "SPLIT": 420,   # ~7 min per GB when splitting across VRAM+RAM
}


def _load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_history(history: dict) -> None:
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception as e:
        log.warning(f"Could not save timeout history: {e}")


def _estimate_first_run_timeout(model: str, memory_mode: str) -> int:
    """Estimate timeout for a model we've never seen before.
    
    Uses model size in the name (e.g. '27b' -> 27GB) and memory mode
    to produce a conservative first-run estimate. This is always
    generous — it's better to wait too long than to kill a valid run.
    """
    # Extract parameter count from model name
    import re
    match = re.search(r'(\d+\.?\d*)b', model.lower())
    param_b = float(match.group(1)) if match else 9.0  # default to 9B if unknown
    
    rate = SECONDS_PER_GB.get(memory_mode, SECONDS_PER_GB["SPLIT"])
    estimated = int(param_b * rate)
    
    log.info(
        f"DYNAMIC TIMEOUT: First-run estimate for {model} in {memory_mode} mode: "
        f"{param_b:.0f}B × {rate}s/GB = {estimated}s ({estimated // 60}m)"
    )
    return max(MIN_TIMEOUT, estimated)


def get_timeout(domain_id: str, tier: str, model: str,
                memory_mode: str = "VRAM", model_size_gb: float = 0.0) -> int:
    """Calculate timeout based on historical completion times.
    
    Logic:
    - If we have history for this domain+tier+mode: use 2.5x max observed
    - If no history: estimate from model size and memory mode
    - Never below MIN_TIMEOUT
    - NO hard ceiling — the system learns from the hardware
    
    Args:
        domain_id: Domain being processed
        tier: Model tier (sprinter/cruiser/heavy)
        model: Model name string
        memory_mode: "VRAM" or "SPLIT" — how the model is loaded
        model_size_gb: Actual model size from Ollama API (optional)
    """
    history = _load_history()
    
    # Key includes memory mode — SPLIT and VRAM have very different speeds
    key = f"{domain_id}:{tier}:{memory_mode}"
    
    # Also check the legacy key format (without memory_mode) for backward compat
    legacy_key = f"{domain_id}:{tier}"
    
    if key in history and history[key].get("completions"):
        times = history[key]["completions"]
        max_time = max(times)
        avg_time = sum(times) / len(times)
        timeout = int(max(max_time * HEADROOM_MULTIPLIER, avg_time * 3))
        timeout = max(MIN_TIMEOUT, timeout)
        log.info(
            f"DYNAMIC TIMEOUT: {key} — {len(times)} samples, "
            f"max={max_time:.0f}s, avg={avg_time:.0f}s, timeout={timeout}s ({timeout // 60}m)"
        )
        return timeout
    
    # Check legacy key
    if legacy_key in history and history[legacy_key].get("completions"):
        times = history[legacy_key]["completions"]
        max_time = max(times)
        # If legacy data exists but this is SPLIT mode, apply a multiplier
        if memory_mode == "SPLIT":
            timeout = int(max_time * HEADROOM_MULTIPLIER * 3)  # SPLIT is ~3x slower
        else:
            timeout = int(max_time * HEADROOM_MULTIPLIER)
        timeout = max(MIN_TIMEOUT, timeout)
        log.info(
            f"DYNAMIC TIMEOUT: {key} — using legacy data from {legacy_key}, "
            f"adjusted timeout={timeout}s ({timeout // 60}m)"
        )
        return timeout
    
    # No history at all — estimate from model size and memory mode
    return _estimate_first_run_timeout(model, memory_mode)


def record_completion(domain_id: str, tier: str, elapsed_seconds: float,
                      memory_mode: str = "VRAM") -> None:
    """Record a successful completion time for future timeout calculations."""
    history = _load_history()
    key = f"{domain_id}:{tier}:{memory_mode}"
    
    if key not in history:
        history[key] = {"completions": [], "timeouts": [], "memory_mode": memory_mode}
    
    history[key]["completions"].append(round(elapsed_seconds, 1))
    history[key]["memory_mode"] = memory_mode
    
    # Keep last 20 samples per key
    history[key]["completions"] = history[key]["completions"][-20:]
    
    _save_history(history)
    log.info(
        f"DYNAMIC TIMEOUT: Recorded {elapsed_seconds:.1f}s completion for {key} "
        f"({elapsed_seconds / 60:.1f}m)"
    )


def record_timeout(domain_id: str, tier: str, timeout_value: int,
                   memory_mode: str = "VRAM") -> None:
    """Record a timeout failure — next run will get more time."""
    history = _load_history()
    key = f"{domain_id}:{tier}:{memory_mode}"
    
    if key not in history:
        history[key] = {"completions": [], "timeouts": [], "memory_mode": memory_mode}
    
    history[key]["timeouts"].append(timeout_value)
    history[key]["timeouts"] = history[key]["timeouts"][-10:]
    
    # If we keep timing out, seed completions with the timeout value
    # so the next run gets at least 2.5x this duration
    if not history[key]["completions"]:
        history[key]["completions"].append(timeout_value)
    else:
        # We timed out even with history — the last timeout IS the new floor
        history[key]["completions"].append(timeout_value)
    
    _save_history(history)
    log.warning(
        f"DYNAMIC TIMEOUT: Recorded timeout at {timeout_value}s ({timeout_value // 60}m) "
        f"for {key}. Future runs will get {int(timeout_value * HEADROOM_MULTIPLIER)}s "
        f"({int(timeout_value * HEADROOM_MULTIPLIER) // 60}m)."
    )
