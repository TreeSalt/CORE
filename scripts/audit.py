#!/usr/bin/env python3
"""
FIDUCIARY AUDITOR TOLLGATE
--------------------------
Performs differential analysis between the current and previous Drop Packet.
Volleys with `forensics.py` to ensure static integrity before auditing deltas.
"""

import re
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DIST_DIR = Path("dist")


def version_key(path: Path):
    return [int(x) for x in re.findall(r"\d+", path.name)]


class FiduciaryAuditor:
    def __init__(self, dist_dir: Path):
        self.dist_dir = dist_dir
        self.red = "\033[91m"
        self.green = "\033[92m"
        self.yellow = "\033[93m"
        self.reset = "\033[0m"

    def run_forensics(self) -> bool:
        """Volley Check: Call forensics.py to verify static integrity first."""
        print(f"{self.yellow}🏸 Volley: Requesting Forensic Audit of current artifacts...{self.reset}")
        result = subprocess.run([sys.executable, "scripts/forensics.py"], capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.returncode != 0:
            print(f"{self.red}❌ Forensic Audit FAILED. Aborting Differential Audit.{self.reset}")
            return False

        # Check for specific success markers in forensics output if needed
        if "CODE != DROP: False" in result.stdout:
            print(f"{self.red}❌ Forensic Volley Returned Corruption Flags (Taxonomy Collision).{self.reset}")
            return False

        print(f"{self.green}✅ Forensic Volley Returned: CLEAN.{self.reset}")
        return True

    def find_artifacts(self) -> Tuple[Optional[Path], Optional[Path]]:
        """Find the two most recent Drop Packets."""
        zips = sorted(list(self.dist_dir.glob("TRADER_OPS_READY_TO_DROP_v*.zip")), key=version_key)
        if not zips:
            return None, None
        if len(zips) == 1:
            return zips[0], None
        return zips[-1], zips[-2]

    def extract_metadata(self, zf: zipfile.ZipFile) -> Dict[str, str]:
        """Extract key-value pairs from Fiduciary Metadata."""
        try:
            data = zf.read("METADATA.txt").decode("utf-8")
            meta = {}
            for line in data.splitlines():
                if ": " in line:
                    key, val = line.split(": ", 1)
                    meta[key.strip().upper()] = val.strip()
                elif "=" in line:
                    key, val = line.split("=", 1)
                    meta[key.strip().upper()] = val.strip()
            # Map legacy keys if needed, but new format uses "Version: ..."
            return meta
        except KeyError:
            return {}

    def audit_versions(self, curr_meta: Dict[str, str], prev_meta: Dict[str, str]) -> bool:
        v_curr = curr_meta.get("VERSION", "0.0.0")
        v_prev = prev_meta.get("VERSION", "0.0.0")

        print(f"📊 Version Transition: {v_prev} -> {v_curr}")
        if v_curr == v_prev:
            print(f"{self.yellow}⚠️  WARNING: Version did not increment.{self.reset}")
            return True  # Not a hard fail, but suspicious

        # Simple SemVer logic check
        # (Could be expanded to strictly enforce Patch vs Minor)
        return True

    def _find_code_zip(self, zf: zipfile.ZipFile) -> Optional[str]:
        for name in zf.namelist():
            if "TRADER_OPS_CODE_v" in name and name.endswith(".zip"):
                return name
        return None

    def compare_code_zips(self, curr_drop: zipfile.ZipFile, prev_drop: zipfile.ZipFile) -> List[str]:
        curr_code_name = self._find_code_zip(curr_drop)
        prev_code_name = self._find_code_zip(prev_drop)

        if not curr_code_name or not prev_code_name:
            print(
                f"{self.yellow}⚠️  Cannot perform Deep Code Audit (Code Code Zip not found in one or both artifacts).{self.reset}"
            )
            return []

        print(f"\n🔬 Deep Code Audit: {prev_code_name} vs {curr_code_name}")

        # Read the nested zips into memory
        curr_code_bytes = curr_drop.read(curr_code_name)
        prev_code_bytes = prev_drop.read(prev_code_name)

        changed_files = []

        with zipfile.ZipFile(BytesIO(curr_code_bytes)) as z_curr, zipfile.ZipFile(BytesIO(prev_code_bytes)) as z_prev:
            curr_files = set(z_curr.namelist())
            prev_files = set(z_prev.namelist())

            # New Files
            new_files = curr_files - prev_files
            for f in sorted(new_files):
                print(f"{self.green}[NEW]  {f}{self.reset}")
                changed_files.append(f)

            # Deleted Files
            del_files = prev_files - curr_files
            for f in sorted(del_files):
                print(f"{self.red}[DEL]  {f}{self.reset}")
                # We can't scan deleted files in forensics, so we don't add them to the scan list

            # Modified Files
            common_files = curr_files.intersection(prev_files)
            for f in sorted(common_files):
                if z_curr.read(f) != z_prev.read(f):
                    print(f"{self.yellow}[MOD]  {f}{self.reset}")
                    if "PAYLOAD_MANIFEST.json" not in f:
                        changed_files.append(f)

        return changed_files

    def compare_zips(self, curr_path: Path, prev_path: Path) -> List[str]:
        print(f"\n🔍 Differential Audit: {prev_path.name} vs {curr_path.name}")

        changed_source_files = []

        with zipfile.ZipFile(curr_path, "r") as z_curr, zipfile.ZipFile(prev_path, "r") as z_prev:
            curr_files = set(z_curr.namelist())
            prev_files = set(z_prev.namelist())

            # Diff the Drop Packet structure
            new_files = curr_files - prev_files
            for f in sorted(new_files):
                print(f"{self.green}[NEW]  {f}{self.reset}")

            del_files = prev_files - curr_files
            for f in sorted(del_files):
                print(f"{self.red}[DEL]  {f}{self.reset}")

            # If Code Zips are present, do deep compare
            changed_source_files = self.compare_code_zips(z_curr, z_prev)

        return changed_source_files

    def run_targeted_forensics(self, files: List[str]):
        if not files:
            print(f"\n{self.green}✨ No source file changes detected. Skipping targeted forensic scan.{self.reset}")
            return

        print(f"\n{self.yellow}🏸 Volley: Requesting Targeted Forensic Scan for {len(files)} files...{self.reset}")
        cmd = [sys.executable, "scripts/forensics.py", "--scan-files"] + files
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print(result.stdout)

        if result.returncode != 0:
            print(f"{self.red}❌ Targeted Forensic Scan FAILED.{self.reset}")
            sys.exit(1)
        print(f"{self.green}✅ Targeted Forensic Scan PASSED.{self.reset}")

    def run(self):
        print("⚖️  FIDUCIARY AUDITOR: INITIALIZING...")

        # 1. Forensic Volley (Static)
        if not self.run_forensics():
            sys.exit(1)

        # 2. Artifact Discovery
        curr, prev = self.find_artifacts()
        if not curr:
            print(f"{self.red}No artifacts found in {self.dist_dir}{self.reset}")
            sys.exit(1)

        if not prev:
            print(
                f"{self.green}🌱 Genesis Audit: First artifact detected ({curr.name}). No history to compare.{self.reset}"
            )
            sys.exit(0)

        # 3. Differential Analysis & Deep Diver
        diff_files = self.compare_zips(curr, prev)

        # 4. Targeted Forensic Volley
        self.run_targeted_forensics(diff_files)

        print("\n✅ Fiduciary Audit Complete.")


if __name__ == "__main__":
    auditor = FiduciaryAuditor(DIST_DIR)
    auditor.run()
