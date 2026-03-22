# antigravity_harness/wal.py
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class WriteAheadLog:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        self.cursor = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS intent_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                intent_type TEXT,
                payload JSON,
                status TEXT
            )
        """)
        self.cursor.execute("PRAGMA synchronous = FULL;")
        self.cursor.execute("PRAGMA journal_mode = WAL;")
        self.cursor.execute("PRAGMA busy_timeout = 5000;")

    def log_intent(self, intent_type: str, payload: dict) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        self.cursor.execute(
            "INSERT INTO intent_log (timestamp, intent_type, payload, status) VALUES (?, ?, ?, ?)",
            (ts, intent_type, json.dumps(payload), "PENDING"),
        )
        return self.cursor.lastrowid

    def commit_intent(self, log_id: int):
        self.cursor.execute("UPDATE intent_log SET status = 'COMMITTED' WHERE id = ?", (log_id,))

    def recover(self):
        self.cursor.execute("SELECT * FROM intent_log WHERE status = 'PENDING'")
        crashes = self.cursor.fetchall()
        if crashes:
            print(f"💀 [RESURRECTION] Found {len(crashes)} uncommitted intents.")

    def prune(self, days_to_keep: int = 30):
        """Hardware Adaptation: Vacuum the WAL to prevent storage bloat."""
        self.cursor.execute(
            "DELETE FROM intent_log WHERE status = 'COMMITTED' AND timestamp < date('now', ?)",
            (f"-{days_to_keep} days",),
        )
        self.cursor.execute("VACUUM")
        print("🧹 [TITAN PRUNING] Released storage space.")
