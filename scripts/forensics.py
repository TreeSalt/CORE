import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import List

DIST_DIR = Path("dist")


def version_key(path: Path):
    return [int(x) for x in re.findall(r"\d+", path.name)]


def get_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_stream(f) -> str:
    sha = hashlib.sha256()
    while chunk := f.read(65536):
        sha.update(chunk)
    return sha.hexdigest()


def scan_files_in_drop(drop_path: Path, files_to_scan: List[str]) -> bool:
    print(f"🔬 FORENSIC DEEP SCAN: Verifying {len(files_to_scan)} changed files in {drop_path.name}...")

    try:
        with zipfile.ZipFile(drop_path, "r") as drop_zip:
            # Find Code Zip
            code_zips = [f for f in drop_zip.namelist() if "TRADER_OPS_CODE_v" in f]
            if not code_zips:
                print("❌ CRITICAL: No Code Zip found in Drop Packet.")
                return False
            code_zip_name = code_zips[0]

            # Open Code Zip (Nested)
            with drop_zip.open(code_zip_name) as code_zip_file, zipfile.ZipFile(code_zip_file, "r") as code_zip:
                # Load Manifest
                try:
                    with code_zip.open("docs/ready_to_drop/PAYLOAD_MANIFEST.json") as f:
                        manifest = json.load(f)
                        file_shas = manifest.get("file_sha256", {})
                except KeyError:
                    print("❌ CRITICAL: Manifest missing from Code Zip.")
                    return False

                all_pass = True
                for file_path in files_to_scan:
                    if file_path not in code_zip.namelist():
                        # Might be a file that was just deleted, so checking it exists in new zip is complex.
                        # If audit says it's [NEW] or [MOD], it MUST be here.
                        print(f"❌ MISSING: {file_path} (Expected in Code Zip)")
                        all_pass = False
                        continue

                    # Verify Hash
                    with code_zip.open(file_path) as f:
                        actual_hash = hash_stream(f)

                    expected_hash = file_shas.get(file_path)
                    if not expected_hash:
                        print(f"⚠️  UNTRACKED: {file_path} (Not in Manifest)")
                        # If it's not in manifest, is it allowed?
                        # Strict Forensic Rule: Everything must be manifest-bound.
                        all_pass = False
                        continue

                    if actual_hash == expected_hash:
                        print(f"   ✅ VERIFIED: {file_path}")
                    else:
                        print(f"   ❌ CORRUPTION: {file_path}")
                        print(f"      Expected: {expected_hash[:8]}")
                        print(f"      Actual:   {actual_hash[:8]}")
                        all_pass = False

                return all_pass

    except Exception as e:
        print(f"❌ FORENSIC ERROR: {e}")
        return False


def main():  # noqa: PLR0912
    parser = argparse.ArgumentParser(description="Fiduciary Forensics")
    parser.add_argument("--scan-files", nargs="+", help="Perform deep manifest verification on specific files")
    args = parser.parse_args()

    if not DIST_DIR.exists():
        print("dist/ does not exist.")
        return

    # If targets provided, switch to Deep Scan Mode
    if args.scan_files:
        # Find latest drop packet
        drops = sorted(list(DIST_DIR.glob("TRADER_OPS_READY_TO_DROP_v*.zip")), key=version_key)
        if not drops:
            print("❌ No Drop Packet found for analysis.")
            sys.exit(1)
        latest_drop = drops[-1]

        success = scan_files_in_drop(latest_drop, args.scan_files)
        sys.exit(0 if success else 1)

    # Default Mode: Dist Artifact Audit
    _run_artifact_audit()


def _run_artifact_audit():
    if not DIST_DIR.exists():
        print("dist/ does not exist.")
        return


def _run_artifact_audit():
    print("artifact | computed_sha256 | sidecar_match | ledger_match | notes")
    print("--- | --- | --- | --- | ---")

    artifacts = sorted([f for f in DIST_DIR.iterdir() if f.is_file()])

    # Load Ledger (Find Latest Versioned)
    ledger_content = {}
    ledger_paths = sorted(DIST_DIR.glob("RUN_LEDGER_v*.json"), key=version_key)
    if ledger_paths:
        ledger_path = ledger_paths[-1]
        print(f"📂 Loading Ledger: {ledger_path.name}")
        ledger_content = json.loads(ledger_path.read_text())
    else:
        print("⚠️ No Ledger found.")

    # Map filename -> ledger sha
    ledger_map = {}
    if "artifacts" in ledger_content:
        for _role, info in ledger_content["artifacts"].items():
            if "filename" in info and "sha256" in info:
                ledger_map[info["filename"]] = info["sha256"]

    drop_hash = ""
    code_hash = ""

    for artifact in artifacts:
        if artifact.name.endswith(".sha256"):
            continue

        computed_sha = get_sha256(artifact)

        # Sidecar check
        sidecar = artifact.with_suffix(artifact.suffix + ".sha256")
        sidecar_match = "N/A"
        if sidecar.exists():
            sidecar_sha = sidecar.read_text().strip().split()[0]
            sidecar_match = "PASS" if sidecar_sha == computed_sha else "FAIL"

        # Ledger check
        ledger_match = "N/A"
        if artifact.name in ledger_map:
            ledger_match = "PASS" if ledger_map[artifact.name] == computed_sha else "FAIL"

        notes = []
        if "READY_TO_DROP_v" in artifact.name:
            drop_hash = computed_sha
        if "CODE_v" in artifact.name:
            code_hash = computed_sha

        print(f"{artifact.name} | {computed_sha} | {sidecar_match} | {ledger_match} | {', '.join(notes)}")

    print("-" * 80)

    # Verdicts
    if code_hash and drop_hash:
        distinct = code_hash != drop_hash
        print(f"CODE != DROP: {distinct} (Code: {code_hash[:8]} vs Drop: {drop_hash[:8]})")


if __name__ == "__main__":
    main()
