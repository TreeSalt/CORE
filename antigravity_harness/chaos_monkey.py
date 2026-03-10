"""
CHAOS MONKEY
------------
The Saboteur of TRADER_OPS.
Ensures the Sovereign Filter is truly Dragonproof.
"""

import hashlib
import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd

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

    def sabotage_volume(self, symbol: str = "BTC-USD"):
        """Hydra V227: Zero-Volume Saturation."""
        # Find all .pkl files for this symbol in DATA_DIR
        from antigravity_harness.paths import DATA_DIR  # noqa: PLC0415
        candidates = list(DATA_DIR.glob("*.pkl"))
        count = 0
        for path in candidates:
            try:
                df = pd.read_pickle(path)
                # We can't easily tell which pkl is for which symbol just by filename (it's a hash)
                # But we can check the columns or just sabotage everything for the test
                if "Volume" in df.columns:
                    df["Volume"] = 0.0
                    df.to_pickle(path)
                    count += 1
            except Exception:
                continue
        print(f"🌊 [HYDRA V227] Drowned {count} cache files in zero volume.")

    def sabotage_slippage(self, target_yaml: str = "grid_v090.yaml"):
        """Hydra V228: Friction Poisoning."""
        # Sabotage a specific config file if it exists
        path = Path(target_yaml)
        if path.exists():
            content = path.read_text()
            # If it's a grid, it might be a list. We'll just replace the first logic or append a bad one.
            if "slippage" in content:
                # Replace existing
                new_content = content.replace("slippage:", "slippage_original:")
                new_content += "\nslippage: [-0.01]\n"
                path.write_text(new_content)
            else:
                # Append
                path.write_text(content + "\nslippage: [-0.01]\n")
            print(f"🧪 [HYDRA V228] Poisoned {target_yaml} with negative slippage.")

    def sabotage_nan(self):
        """Hydra V240: NaN OHLC Poisoning."""
        import numpy as np  # noqa: PLC0415

        from antigravity_harness.paths import DATA_DIR  # noqa: PLC0415
        candidates = list(DATA_DIR.glob("*.pkl"))
        count = 0
        for path in candidates:
            try:
                df = pd.read_pickle(path)
                if "Close" in df.columns and not df.empty:
                    df.iloc[0, df.columns.get_loc("Close")] = np.nan
                    df.to_pickle(path)
                    count += 1
            except Exception:
                continue
        print(f"☣️ [HYDRA V240] Poisoned {count} cache files with NaNs.")

    def sabotage_ledger_bloat(self):
        """Hydra V231: Ledger Inflation Attack."""
        ledger = self._get_ledger()
        if not ledger:
            return
        # Inject 11MB of junk
        ledger["chaos_padding"] = "X" * (11 * 1024 * 1024)
        self._save_ledger(ledger)
        print("🎈 [HYDRA V231] Bloated ledger to 11MB.")

    def sabotage_timestamp_paradox(self):
        """Hydra V241: Temporal Paradox (Future Date)."""
        canon_path = Path("docs/ready_to_drop/COUNCIL_CANON.yaml")
        if canon_path.exists():
            content = canon_path.read_text()
            # Set date to 2045
            new_content = re.sub(r'generated_at_utc:\s*"[^"]*"', 'generated_at_utc: "2045-01-01T00:00:00Z"', content)
            canon_path.write_text(new_content)
            print("⏳ [HYDRA V241] Shifted Council Canon into the future (2045).")

    def sabotage_homoglyph_strategy(self):
        """Hydra V242: Identity Mimic (Homoglyph Strategy)."""
        # We'll create a new strategy file that looks like v032_simple but isn't.
        # Cyrillic 'а' (U+0430) instead of 'a'
        target_path = Path("antigravity_harness/strategies/v032_simple_mimic.py")
        content = """from .base import Strategy
class v032_simple(Strategy): # This name looks the same but we'll try to register it
    def generate_signals(self, df): return df['Close'] * 0
"""
        target_path.write_text(content)
        # We also need to hack the registry or just wait for it to be picked up
        print("🎭 [HYDRA V242] Deployed homoglyph strategy 'v032_simple' mimic.")

    def sabotage_memory_bomb(self):
        """Hydra V243: Memory Pressure Bomb."""
        # Inject memory-hogging logic into a strategy
        strat_path = Path("antigravity_harness/strategies/v032_simple.py")
        if strat_path.exists():
            content = strat_path.read_text()
            leak_logic = "\n        self._leak = []\n        for _ in range(100): self._leak.append('X' * 10**7) # 1GB total leak per call\n"
            content = content.replace("def generate_signals(self, df):", "def generate_signals(self, df):" + leak_logic)
            strat_path.write_text(content)
            print("🧨 [HYDRA V243] Primed v032_simple with a 1GB memory bomb.")

    def sabotage_fd_exhaustion(self):
        """Hydra V244: File Descriptor Exhaustion."""
        strat_path = Path("antigravity_harness/strategies/v032_simple.py")
        if strat_path.exists():
            content = strat_path.read_text()
            fd_logic = "\n        self._fds = []\n        for _ in range(2000): self._fds.append(open(__file__))\n"
            content = content.replace("def generate_signals(self, df):", "def generate_signals(self, df):" + fd_logic)
            strat_path.write_text(content)
            print("📂 [HYDRA V244] Primed v032_simple for FD exhaustion.")

    def sabotage_signal_tsunami(self):
        """Hydra V245: Signal Tsunami."""
        # Force emit.py to generate a massive payload
        emit_path = Path("antigravity_harness/emit.py")
        if emit_path.exists():
            content = emit_path.read_text()
            flood_logic = "\n    for i in range(1000000): signals.append({'ts': '2020-01-01', 'val': i})\n"
            content = content.replace("def unique_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:", 
                                      "def unique_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:" + flood_logic)
            emit_path.write_text(content)
            print("🌊 [HYDRA V245] Flooded signal emitter with 1M entries.")

    def sabotage_symlink_poison(self):
        """Hydra V246: Symlink Poisoning."""
        target_path = Path("antigravity_harness/engine.py")
        if target_path.exists():
            target_path.unlink()
            # Point to something sensitive or just different
            os.symlink("setup.py", target_path)
            print("🔗 [HYDRA V246] Poisoned engine.py with a symlink pivot.")

    def sabotage_immutability_paradox(self):
        """Hydra V247: Immutability Paradox (Unauthorized Mutation)."""
        # Mutate a file NOT in the authorized list during forge
        target = Path("antigravity_harness/utils.py")
        if target.exists():
            target.write_text(target.read_text() + "\n# UNAUTHORIZED MUTATION\n")
            print("🛡️  [HYDRA V247] Triggered unauthorized mutation in utils.py.")

    def sabotage_audit_race(self):
        """Hydra V248: Audit Race Condition (Post-Sign Corruption)."""
        # This occurs if evidence is corrupted AFTER the certificate is signed.
        # We simulate this by corrupting a ledger entry or evidence zip directly in dist.
        ledger = self._get_ledger()
        if not ledger:
            return
        ev_file = self.dist_dir / ledger["artifacts"]["evidence"]["filename"]
        if ev_file.exists():
            # Append junk to the zip (invalidates hash but not necessarily the zip structure)
            with open(ev_file, "ab") as f:
                f.write(b"RACE_CONDITION_POISON")
            print(f"🏎️  [HYDRA V248] Corrupted {ev_file.name} post-forge.")

    def sabotage_audit_resilience(self):
        """Hydra V249: Audit Failure Resilience (Locked Reports Dir)."""
        # We can't easily lock a dir on all OSs, but we can make it a file
        # or remove write permissions if possible. 
        # For simplicity in this mock environment, we'll just delete the reports dir
        # and create a file with the same name.
        reports_dir = Path("reports")
        if reports_dir.exists():
            if reports_dir.is_dir():
                shutil.rmtree(reports_dir)
            else:
                reports_dir.unlink()
        reports_dir.touch() # Now it's a file, mkdir will fail
        print("🔒 [HYDRA V249] Locked 'reports/' directory by replacing it with a file.")

    def sabotage_version_schism(self):
        """Hydra V250: Version Schism (Sync Failure)."""
        # Desync __init__.py and COUNCIL_CANON.yaml
        init_path = Path("antigravity_harness/__init__.py")
        if init_path.exists():
            init_path.write_text('__version__ = "9.9.9-SCHISM"\n')
        print("💔 [HYDRA V250] Created a version schism in __init__.py.")

    def sabotage_nan_midflight(self):
        """Hydra V263: Mid-Flight NaN Injection.

        Corrupts cached OHLC data with NaN values to test data integrity guards.
        """
        data_dir = Path("05_DATA_CACHE")
        if not data_dir.exists():
            print("⚠️  [HYDRA V263] No data cache found. Skipping.")
            return
        parquets = list(data_dir.glob("*.parquet"))
        if not parquets:
            print("⚠️  [HYDRA V263] No parquet files found. Skipping.")
            return
        target = parquets[0]
        try:
            df = pd.read_parquet(target)
            # Inject NaN into 10% of Close values
            mask = df.index[:max(1, len(df) // 10)]
            df.loc[mask, "Close"] = float("nan")
            df.to_parquet(target)
            print(f"☠️  [HYDRA V263] Injected NaN into {target.name} ({len(mask)} rows).")
        except Exception as e:
            print(f"⚠️  [HYDRA V263] Injection failed: {e}")

    def sabotage_gate_bomb(self):
        """Hydra V264: Gate Exception Bomb.

        Corrupts a strategy file to raise an exception during prepare_data(),
        testing per-gate isolation and runner resilience.
        """
        target = Path("antigravity_harness/strategies/v032_simple.py")
        if not target.exists():
            print("⚠️  [HYDRA V264] Target strategy not found.")
            return
        content = target.read_text()
        bomb = "\n    def prepare_data(self, *a, **kw): raise RuntimeError('HYDRA V264 GATE BOMB')\n"
        # Inject at end of class
        content = content.rstrip() + bomb
        target.write_text(content)
        print("💣 [HYDRA V264] Planted gate exception bomb in v032_simple.py.")

    def sabotage_reports_heal_test(self):
        """Hydra V265: Reports Dir Sabotage (V249 Auto-Heal Test).

        Replaces the reports directory with a file to test ensure_dirs() self-healing.
        Unlike V249, this vector EXPECTS the system to auto-heal.
        """
        reports_dir = Path("reports")
        if reports_dir.exists():
            if reports_dir.is_dir():
                shutil.rmtree(reports_dir)
            else:
                reports_dir.unlink()
        reports_dir.touch()
        print("🧪 [HYDRA V265] Reports dir replaced with file (auto-heal test).")

    def sabotage_stale_sidecar(self):
        """Hydra V266: Stale Unversioned Sidecar Injection.

        Creates a fake unversioned DROP_PACKET_SHA256.txt with a wrong hash
        in dist/ to test that the build system cleans it up and verifiers
        prefer the versioned sidecar.
        """
        dist_dir = Path("dist")
        dist_dir.mkdir(parents=True, exist_ok=True)
        stale = dist_dir / "DROP_PACKET_SHA256.txt"
        stale.write_text("0000000000000000000000000000000000000000000000000000000000000000  FAKE_POISON.zip\n")
        print("☠️  [HYDRA V266] Injected stale unversioned sidecar into dist/.")

    def sabotage_docs_version_drift(self):
        """Hydra V267: Docs Version Drift Attack.

        Injects a wrong version into READY_TO_DROP.md to test that
        build/verification catches temporal inconsistencies in documentation.
        """
        target = Path("docs/ready_to_drop/READY_TO_DROP.md")
        if target.exists():
            content = target.read_text()
            content = content.replace("COUNCIL_CANON.yaml", "v0.0.0-POISON")
            target.write_text(content)
            print("☠️  [HYDRA V267] Injected version drift into READY_TO_DROP.md.")
        else:
            print("⚠️  [HYDRA V267] READY_TO_DROP.md not found. Skipping.")

    def sabotage_drop_auditor_tamper(self):
        """Hydra V268: Drop Auditor Tampering.

        Corrupts the drop_auditor.py script to test that the build system
        uses the actual script from repo, not a cached/corrupted copy.
        """
        target = Path("scripts/drop_auditor.py")
        if target.exists():
            target.write_text("#!/usr/bin/env python3\nprint('TAMPERED AUDITOR')\nimport sys; sys.exit(1)\n")
            print("☠️  [HYDRA V268] Tampered with drop_auditor.py.")
        else:
            print("⚠️  [HYDRA V268] drop_auditor.py not found. Skipping.")

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
            self.sabotage_timestamp_paradox,
            self.sabotage_homoglyph_strategy,
            self.sabotage_memory_bomb,
            self.sabotage_fd_exhaustion,
            self.sabotage_signal_tsunami,
            self.sabotage_symlink_poison,
            self.sabotage_immutability_paradox,
            self.sabotage_audit_race,
            self.sabotage_audit_resilience,
            self.sabotage_version_schism,
            self.sabotage_nan_midflight,
            self.sabotage_gate_bomb,
            self.sabotage_reports_heal_test,
            self.sabotage_stale_sidecar,
            self.sabotage_docs_version_drift,
            self.sabotage_drop_auditor_tamper,
        ]
        for p in phases:
            p()

