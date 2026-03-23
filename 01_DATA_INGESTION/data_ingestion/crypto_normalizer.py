"""Crypto data normalizer — timestamp, volume, gap-fill, integrity checks."""
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)


def normalize_timestamps(candles: list, input_format: str = "unix_s") -> list:
    result = []
    for c in candles:
        ts = c["timestamp"]
        if input_format == "unix_ms":
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        result.append({**c, "timestamp": dt.isoformat()})
    return result


def normalize_volume(candles: list, denomination: str = "base") -> list:
    if denomination == "base":
        return candles
    result = []
    for c in candles:
        price = c.get("close", 1)
        vol = c["volume"] / price if price > 0 else 0
        result.append({**c, "volume": round(vol, 6)})
    return result


def fill_gaps(candles: list, method: str = "ffill") -> list:
    if not candles:
        return candles
    if method == "drop":
        return [c for c in candles if c.get("volume", 0) > 0]
    filled = [candles[0]]
    for c in candles[1:]:
        if c.get("volume", 0) == 0:
            prev = filled[-1]
            filled.append({**c, "open": prev["close"], "high": prev["close"],
                          "low": prev["close"], "close": prev["close"]})
            log.warning(f"Gap filled at {c.get('timestamp', '?')}")
        else:
            filled.append(c)
    return filled


def validate_integrity(candles: list) -> dict:
    issues = []
    now_ts = datetime.now(timezone.utc).timestamp()
    prev_ts = None
    for i, c in enumerate(candles):
        ts = c.get("timestamp", 0)
        if isinstance(ts, str):
            continue
        if ts > now_ts:
            issues.append(f"Future timestamp at index {i}: {ts}")
        if prev_ts is not None and ts < prev_ts:
            issues.append(f"Non-monotonic at index {i}: {ts} < {prev_ts}")
        if any(c.get(k, 0) < 0 for k in ("open", "high", "low", "close", "volume")):
            issues.append(f"Negative value at index {i}")
        prev_ts = ts
    return {"valid": len(issues) == 0, "issue_count": len(issues), "issues": issues}
