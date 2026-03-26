"""Dynamic timeout manager — learns from past execution times.

Never cuts off a model mid-generation. Instead, uses historical
completion times per domain+tier to set intelligent timeouts.

Design: the creative models get as much time as they need.
The system adapts to them, not the other way around.
"""
import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

HISTORY_FILE = Path(__file__).resolve().parent / "timeout_history.json"
DEFAULT_TIMEOUT = 1200  # 15 min baseline — generous default
MIN_TIMEOUT = 900      # 5 min floor
MAX_TIMEOUT = 3600     # 60 min ceiling
HEADROOM_MULTIPLIER = 2.0  # Give 2x the longest observed time


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


def get_timeout(domain_id: str, tier: str, model: str) -> int:
    """Calculate timeout based on historical completion times.
    
    Logic:
    - If we have history for this domain+tier: use 2x the max observed time
    - If no history: use generous default (900s)
    - Never below MIN_TIMEOUT, never above MAX_TIMEOUT
    - 27B+ models always get MAX_TIMEOUT (they're in SPLIT mode)
    """
    # Heavy models in SPLIT mode always get maximum time
    if any(size in model for size in ("27b", "30b", "32b", "35b", "70b")):
        log.info(f"DYNAMIC TIMEOUT: {model} is heavy — using max timeout {MAX_TIMEOUT}s")
        return MAX_TIMEOUT

    history = _load_history()
    key = f"{domain_id}:{tier}"
    
    if key in history and history[key]["completions"]:
        times = history[key]["completions"]
        max_time = max(times)
        avg_time = sum(times) / len(times)
        timeout = int(max(max_time * HEADROOM_MULTIPLIER, avg_time * 3))
        timeout = max(MIN_TIMEOUT, min(MAX_TIMEOUT, timeout))
        log.info(
            f"DYNAMIC TIMEOUT: {key} — {len(times)} samples, "
            f"max={max_time:.0f}s, avg={avg_time:.0f}s, timeout={timeout}s"
        )
        return timeout
    
    log.info(f"DYNAMIC TIMEOUT: {key} — no history, using default {DEFAULT_TIMEOUT}s")
    return DEFAULT_TIMEOUT


def record_completion(domain_id: str, tier: str, elapsed_seconds: float) -> None:
    """Record a successful completion time for future timeout calculations."""
    history = _load_history()
    key = f"{domain_id}:{tier}"
    
    if key not in history:
        history[key] = {"completions": [], "timeouts": []}
    
    history[key]["completions"].append(round(elapsed_seconds, 1))
    
    # Keep last 20 samples per key
    history[key]["completions"] = history[key]["completions"][-20:]
    
    _save_history(history)
    log.info(f"DYNAMIC TIMEOUT: Recorded {elapsed_seconds:.1f}s completion for {key}")


def record_timeout(domain_id: str, tier: str, timeout_value: int) -> None:
    """Record a timeout failure — next run will get more time."""
    history = _load_history()
    key = f"{domain_id}:{tier}"
    
    if key not in history:
        history[key] = {"completions": [], "timeouts": []}
    
    history[key]["timeouts"].append(timeout_value)
    history[key]["timeouts"] = history[key]["timeouts"][-10:]
    
    # If we keep timing out, bump future completions estimate
    if not history[key]["completions"]:
        # No successful completions — seed with the timeout value as a floor
        history[key]["completions"].append(timeout_value)
    
    _save_history(history)
    log.warning(
        f"DYNAMIC TIMEOUT: Recorded timeout at {timeout_value}s for {key}. "
        f"Future runs will get more time."
    )
