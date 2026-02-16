#!/usr/bin/env python3
"""
THE INTELLIGENCE INGESTOR (The Sensory Organ)
--------------------------------------------
Collects raw essence from the digital aether, signs it,
and commits it to the Truth Ledger.

Motto: "Truth is found in the raw, not the processed."
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import httpx

# Paths
INTEL_DIR = Path("intelligence")
RAW_DIR = INTEL_DIR / "raw"
LEDGER_FILE = INTEL_DIR / "ledger.json"

# Sources (The Source Registry)
SOURCES = {
    "MARKET_PULSE": {
        "url": "https://www.cnn.com/markets/fear-and-greed",
        "type": "html",
        "parser": "parse_cnn_fear_greed",
    },
    "MARKET_ALPHA": {
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "type": "rss",
        "parser": "parse_market_alpha",
    },
}


def get_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class IntelligenceIngestor:
    def __init__(self):
        self._init_dirs()
        self.client = httpx.Client(timeout=10.0)

    def _init_dirs(self):
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        if not LEDGER_FILE.exists():
            LEDGER_FILE.write_text(json.dumps({"entries": []}, indent=4))

    def gurgle(self, source_id: str):
        source = SOURCES.get(source_id)
        if not source:
            print(f"❌ Unknown source: {source_id}")
            return

        print(f"📡 GURGLING: {source_id} ({source['url']})...")

        try:
            resp = self.client.get(source["url"])
            resp.raise_for_status()
            
            # HYDRA GUARD: Large File SABOTAGE (Vector 43)
            # Rejects oversized raw assets to prevent disk exhaustion
            raw_data = resp.content
            if len(raw_data) > 1024 * 1024 * 100: # 100 MB limit
                raise RuntimeError(f"CONTENT OVERSIZE: {source_id} retrieved {len(raw_data)} bytes. Threshold: 100MB.")

            # 1. Cryptographic Binding (Sovereign Hash)
            sha = get_sha256(raw_data)
            timestamp = int(time.time())

            # 2. Commit to Raw Storage
            raw_file = RAW_DIR / f"{source_id}_{timestamp}_{sha[:8]}.html"
            raw_file.write_bytes(raw_data)

            # 3. Update Truth Ledger
            self._update_ledger(source_id, timestamp, sha, str(raw_file))

            print(f"✅ SECURED: {sha[:16]} committed to Ledger.")
            return raw_data

        except Exception as e:
            print(f"❌ INGESTION FAILED: {source_id} -> {e}")
            return None

    def _update_ledger(self, source_id: str, timestamp: int, sha: str, path: str):
        # HYDRA GUARD: Atomic State Update (Vector 42)
        if LEDGER_FILE.exists():
            with open(LEDGER_FILE, "r") as f:
                ledger = json.load(f)
        else:
            ledger = {"entries": []}

        # HYDRA GUARD: Time Reverse Protection (Vector 120)
        # Ensure new entry has a timestamp >= latest entry for this source
        source_entries = [e for e in ledger["entries"] if e["source"] == source_id]
        if source_entries:
            latest = max(e["timestamp"] for e in source_entries)
            if timestamp < latest:
                raise RuntimeError(f"TEMPORAL ANOMALY: {source_id} timestamp {timestamp} < latest {latest}. Possible replay attack.")

        # HYDRA GUARD: Flash Crash / Anomaly Guard (Vector 107)
        # (Placeholder for content-based anomaly detection)
        # if self._detect_anomaly(source_id, raw_data): ...

        entry = {
            "source": source_id,
            "timestamp": timestamp,
            "sha256": sha,
            "path": path,
            "type": SOURCES[source_id]["type"],
        }
        ledger["entries"].append(entry)
        
        tmp_ledger = LEDGER_FILE.with_suffix(".tmp")
        with open(tmp_ledger, "w") as f:
            json.dump(ledger, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(tmp_ledger, LEDGER_FILE)


from antigravity_harness.essence import parse_cnn_fear_greed


if __name__ == "__main__":
    ingestor = IntelligenceIngestor()
    # Gurgle Market Pulse
    ingestor.gurgle("MARKET_PULSE")
