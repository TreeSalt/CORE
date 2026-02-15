import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from antigravity_harness.wal import WriteAheadLog


class PhoenixProtocol:
    """
    The Phoenix Protocol: Verifies Write-Ahead Log (WAL) resilience.
    Orchestrates a self-destructing process and verifies intent recovery.
    """

    def __init__(self, db_path: str = "phoenix_test.db"):
        self.db_path = Path(db_path)

    def run_victim(self) -> None:
        """
        The Victim: A process that intends to do work but dies.
        """
        # Create WAL
        wal = WriteAheadLog(self.db_path)
        print("🔥 [VICTIM] Logging fatal intent...")

        # Log an intent
        intent_id = wal.log_intent("PHOENIX_RISING", {"secret": "The Ash Remains"})
        print(f"🔥 [VICTIM] Intent {intent_id} logged. Status: PENDING.")

        # Force WAL flush to disk before death
        wal.conn.commit()

        # Simulate work
        time.sleep(0.5)

        # SIMULATE SUDDEN DEATH (Self-SIGKILL)
        print("🔥 [VICTIM] Committing seppuku (SIGKILL)...")
        os.kill(os.getpid(), signal.SIGKILL)

    def run_survivor(self, wrapper_script_path: str) -> None:
        """
        The Survivor: Spawns the victim and checks the ashes.
        """
        self._cleanup()

        print("🦅 [PHOENIX] Spawning victim process...")

        # Run victim in separate process using the same python executable
        # We pass 'run_victim' as argument to the wrapper script
        cmd = [sys.executable, wrapper_script_path, "run_victim"]

        # Run and wait
        proc = subprocess.run(cmd, check=False)

        # Verify return code (should differ based on OS but usually non-zero)
        print(f"🦅 [PHOENIX] Victim died with return code {proc.returncode}.")

        # Verify Resurrection
        self._verify_ashes()
        self._cleanup()
        print("🧹 [PHOENIX] Ashes swept away.")

    def _verify_ashes(self) -> None:
        print("🦅 [PHOENIX] Inspecting the ashes (WAL Recovery)...")
        wal = WriteAheadLog(self.db_path)

        # Manually inspect DB to see if PENDING state exists
        wal.cursor.execute("SELECT * FROM intent_log WHERE status = 'PENDING'")
        rows = wal.cursor.fetchall()

        if not rows:
            print("❌ [PHOENIX FAILED] The intent was lost in the fire.")
            sys.exit(1)

        found_secret = False
        for row in rows:
            print(f"✨ [PHOENIX RISES] Recovered Intent: {row}")
            # Schema: (id, timestamp, intent_type, payload, status)
            try:
                payload = json.loads(row[3])
                if payload.get("secret") == "The Ash Remains":
                    print("✅ [TITAN APPROVED] WAL Persistence Verified.")
                    found_secret = True
            except Exception as e:
                print(f"Error parsing payload: {e}")

        if not found_secret:
            print("❌ [PHOENIX FAILED] Intent found but payload mismatch.")
            sys.exit(1)

    def _cleanup(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

        wal_path = self.db_path.with_suffix(".db-wal")
        if wal_path.exists():
            wal_path.unlink()

        shm_path = self.db_path.with_suffix(".db-shm")
        if shm_path.exists():
            shm_path.unlink()
