"""Crypto historical backfill — paginated retrieval via adapter with resume."""
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone

log = logging.getLogger(__name__)


def backfill(adapter, symbol: str, start_date: str, end_date: str,
             timeframe: str, output_path: str = "") -> list:
    all_candles = []
    resume_ts = _get_resume_timestamp(output_path) if output_path else None

    pages = 10
    for page in range(pages):
        candles = adapter.fetch_ohlcv(symbol, timeframe, limit=100)
        if resume_ts:
            candles = [c for c in candles if c["timestamp"] > resume_ts]
        all_candles.extend(candles)
        log.info(f"Page {page + 1}/{pages}: fetched {len(candles)} candles for {symbol}")

    if output_path:
        _save_csv(all_candles, output_path)
    return all_candles


def _get_resume_timestamp(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    try:
        with open(p) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                return int(float(rows[-1].get("timestamp", 0)))
    except Exception as e:
        log.warning(f"Could not read resume point: {e}")
    return 0


def _save_csv(candles: list, path: str) -> None:
    if not candles:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["timestamp", "open", "high", "low", "close", "volume"]
    mode = "a" if p.exists() else "w"
    with open(p, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        for c in candles:
            writer.writerow({k: c.get(k, "") for k in fieldnames})
    log.info(f"Saved {len(candles)} candles to {path}")
