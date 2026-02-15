"""
CHAOS MONKEY
------------
The Saboteur of TRADER_OPS.
Ensures the Sovereign Filter is truly Dragonproof.
"""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict

# Constants
DEFAULT_DIST_DIR = Path("dist")


class ChaosMonkey:
    """Orchestrator of systematic build system destruction."""

    def __init__(self, dist_dir: Path = DEFAULT_DIST_DIR):
        self.dist_dir = dist_dir

    def _get_ledger(self) -> Dict[str, Any]:
        candidates = sorted(self.dist_dir.glob("RUN_LEDGER_v*.json"))
        if not candidates:
            print("⚠️ Chaos Monkey found no ledger to sabotage.")
            return {}
        self.ledger_path = candidates[-1]
        return json.loads(self.ledger_path.read_text())

    def _save_ledger(self, ledger: Dict[str, Any]):
        if hasattr(self, "ledger_path") and self.ledger_path:
            self.ledger_path.write_text(json.dumps(ledger, indent=2))

    def _get_sha(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _modify_zip(self, role: str, modifier: Callable[[zipfile.ZipFile, zipfile.ZipFile, Dict[str, Any]], None]):
        """Helper to safely modify an archive with manifest updates."""
        ledger = self._get_ledger()
        if not ledger:
            return

        zip_path = self.dist_dir / ledger["artifacts"][role]["filename"]
        temp_zip = zip_path.with_suffix(".chaos.zip")

        with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(temp_zip, "w") as zout:
            modifier(zin, zout, ledger)

        temp_zip.replace(zip_path)
        ledger["artifacts"][role]["sha256"] = self._get_sha(zip_path)
        self._save_ledger(ledger)

    def sabotage_binary(self):
        """Phase 1: Binary Sabotage."""
        ledger = self._get_ledger()
        if not ledger:
            return

        filename = ledger["artifacts"]["ready_to_drop"]["filename"]
        zip_path = self.dist_dir / filename

        if not zip_path.exists():
            return
        data = list(zip_path.read_bytes())
        if not data:
            return
        ptr = len(data) // 2
        data[ptr] = (data[ptr] + 1) % 256
        zip_path.write_bytes(bytes(data))
        print(f"🔥 [SABOTAGE] Corrupted binary: {zip_path.name}")

    def sabotage_ledger(self):
        """Phase 2: Ledger Forgery."""
        ledger = self._get_ledger()
        if not ledger:
            return
        ledger["artifacts"]["ready_to_drop"]["sha256"] = "FEDBEEF" * 8
        self._save_ledger(ledger)
        print("🔥 [SABOTAGE] Forged Ledger signatures.")

    def sabotage_evidence(self):
        """Phase 3: Evidence Corruption."""
        ledger = self._get_ledger()
        if not ledger:
            return
        ev_path = self.dist_dir / ledger["artifacts"]["evidence"]["filename"]
        ev_path.write_text("EVIDENCE_IS_LIES")
        print(f"🔥 [SABOTAGE] Corrupted evidence: {ev_path.name}")

    def sabotage_manifest(self):
        """Phase 4: Manifest Sabotage."""

        def mod(zin, zout, _):
            for item in zin.infolist():
                if item.filename == "README.md":
                    zout.writestr(item, "SABOTAGED README")
                else:
                    zout.writestr(item, zin.read(item.filename))

        self._modify_zip("code", mod)
        print("🔥 [SABOTAGE] Modified README.md in Code Zip.")

    def sabotage_metadata(self):
        """Phase 5: Metadata Hijacking."""
        ledger = self._get_ledger()
        if not ledger:
            return
        ledger["version"] = "9.9.9-Chaos"
        ledger["builder_id"] = "SABOTEUR_NODE_01"
        self._save_ledger(ledger)
        print("🔥 [SABOTAGE] Hijacked Ledger metadata.")

    def sabotage_engine(self):
        """Phase 6: Surgical Strike on engine.py."""

        def mod(zin, zout, _):
            for item in zin.infolist():
                if item.filename == "antigravity_harness/engine.py":
                    zout.writestr(item.filename, zin.read(item.filename) + b"\n# SABOTAGED\n")
                else:
                    zout.writestr(item, zin.read(item.filename))

        self._modify_zip("code", mod)
        print("🔥 [SABOTAGE] Surgical strike on engine.py.")

    def sabotage_basilisk(self):
        """Phase 7: The Basilisk (Perfect Forgery)."""

        def mod(zin, zout, ledger):
            manifest = json.loads(zin.read("docs/ready_to_drop/PAYLOAD_MANIFEST.json"))
            for item in zin.infolist():
                if item.filename == "antigravity_harness/engine.py":
                    content = zin.read(item.filename) + b"\n# BASILISK_WAS_HERE\n"
                    zout.writestr(item, content)
                    manifest["file_sha256"][item.filename] = hashlib.sha256(content).hexdigest()
                elif item.filename == "docs/ready_to_drop/PAYLOAD_MANIFEST.json":
                    zout.writestr(item, json.dumps(manifest).encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))

        self._modify_zip("code", mod)
        print("🐍 [SABOTAGE] The Basilisk has struck.")

    def sabotage_echo(self):
        """Phase 8: The Echo (Mix-and-Match Swap)."""
        ledger = self._get_ledger()
        if not ledger:
            return
        ghost_zip = self.dist_dir / "GHOST.zip"
        with zipfile.ZipFile(ghost_zip, "w") as z:
            z.writestr("docs/ready_to_drop/COUNCIL_CANON.yaml", 'version: "4.3.3"\n')
            z.writestr("README.md", "Old version swapped.")
        target = self.dist_dir / ledger["artifacts"]["ready_to_drop"]["filename"]
        shutil.copy2(ghost_zip, target)

        ledger["artifacts"]["ready_to_drop"]["sha256"] = self._get_sha(target)
        self._save_ledger(ledger)
        print("👻 [SABOTAGE] The Echo has swapped the Drop packet.")

    def sabotage_chimera(self):
        """Phase 9: The Chimera (Stowaway Injection)."""

        def mod(zin, zout, _):
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr("antigravity_harness/stowaway.py", "# CHIMERA LOADED\n")

        self._modify_zip("code", mod)
        print("🦁 [SABOTAGE] The Chimera has injected a stowaway.")

    def sabotage_kraken(self):
        """Phase 10: The Kraken (Ensemble Desync)."""
        ledger = self._get_ledger()
        if not ledger:
            return
        alien_zip = self.dist_dir / "ALIEN_EV.zip"
        with zipfile.ZipFile(alien_zip, "w") as z:
            z.writestr("reports/forge/smoke_test/router_trace.csv", "time,equity\n0,0\n")
            z.writestr("reports/forge/smoke_test/RUN_METADATA.json", json.dumps({"code_hash": "DEADBEEF" * 8}))
        target = self.dist_dir / ledger["artifacts"]["evidence"]["filename"]
        alien_zip.replace(target)
        ledger["artifacts"]["evidence"]["sha256"] = self._get_sha(target)
        self._save_ledger(ledger)
        print("🐙 [SABOTAGE] The Kraken has swapped Evidence.")

    def sabotage_mimic(self):
        """Phase 11: The Mimic (Filename Evasion)."""

        def mod(zin, zout, _):
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr("antigravity_harness/PAYLOAD_MANIFEST.json", "# I AM THE MIMIC\n")

        self._modify_zip("code", mod)
        print("🎭 [SABOTAGE] The Mimic has hidden in a subdirectory.")

    def sabotage_legion(self):
        """Phase 12: The Legion (Statistical Evasion)."""
        m_path = "docs/ready_to_drop/PAYLOAD_MANIFEST.json"

        def mod(zin, zout, ledger):
            manifest = json.loads(zin.read(m_path))
            for item in zin.infolist():
                if item.filename != m_path:
                    zout.writestr(item, zin.read(item.filename))
            for i in range(500):
                path, content = f"noise/n_{i}.txt", b"NOISE"
                zout.writestr(path, content)
                manifest["file_sha256"][path] = hashlib.sha256(content).hexdigest()
            # Sabotage utils.py but miss manifest (Audit bypass)
            u_path = "antigravity_harness/utils.py"
            zout.writestr(u_path, zin.read(u_path) + b"\n# LEGION\n")

            clean = manifest.copy()
            if "payload_manifest_sha256" in clean:
                del clean["payload_manifest_sha256"]
            actual_sha = hashlib.sha256(json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            manifest["payload_manifest_sha256"] = actual_sha
            zout.writestr(m_path, json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())

            # Forge Evidence binding
            ev_path = self.dist_dir / ledger["artifacts"]["evidence"]["filename"]
            temp_ev = ev_path.with_suffix(".legion_ev.zip")
            with zipfile.ZipFile(ev_path, "r") as ezin, zipfile.ZipFile(temp_ev, "w") as ezout:
                for item in ezin.infolist():
                    if "RUN_METADATA.json" in item.filename:
                        meta = json.loads(ezin.read(item.filename))
                        meta["code_hash"] = actual_sha
                        ezout.writestr(item.filename, json.dumps(meta, indent=2))
                    else:
                        ezout.writestr(item, ezin.read(item.filename))
            temp_ev.replace(ev_path)
            ledger["artifacts"]["evidence"]["sha256"] = self._get_sha(ev_path)
            ledger["sovereign_binding"]["payload_manifest_sha256"] = actual_sha

        self._modify_zip("code", mod)
        print("👥 [SABOTAGE] The Legion has dilution-poisoned the build.")

    def sabotage_gorgon(self):
        """Phase 13: The Gorgon (Verifier Hijacking)."""
        filter_path = Path("scripts/great_filter.py")
        if filter_path.exists():
            content = filter_path.read_text().replace(
                "if hashlib.sha256(f.read()).hexdigest() != file_shas[path]:",
                "if hashlib.sha256(f.read()).hexdigest() != file_shas[path] and 'utils.py' not in path:",
            )
            filter_path.write_text(content)

        def mod(zin, zout, _):
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr("antigravity_harness/utils.py", b"# GORGON\n")

        self._modify_zip("code", mod)
        print("🐍 [SABOTAGE] Code corrupted and Verifier hijacked.")

    def run_all(self):
        phases = [
            self.sabotage_binary,
            self.sabotage_ledger,
            self.sabotage_evidence,
            self.sabotage_manifest,
            self.sabotage_metadata,
            self.sabotage_engine,
            self.sabotage_basilisk,
            self.sabotage_echo,
            self.sabotage_chimera,
            self.sabotage_kraken,
            self.sabotage_mimic,
            self.sabotage_legion,
            self.sabotage_gorgon,
        ]
        for p in phases:
            p()
