#!/usr/bin/env python3
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

# Add repo root to path for imports
repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root))

from antigravity_harness.utils import infer_periods_per_year  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def version_key(path: Path):
    """Sort key for versioned filenames (vX.Y.Z)."""
    # Extract all numbers, map to int
    # e.g. TRADER_OPS_READY_TO_DROP_v4.4.10.zip -> [4, 4, 10]
    return [int(x) for x in re.findall(r"\d+", path.name)]


def print_pass(msg):
    print(f"{GREEN}PASS{RESET} {msg}")


def print_fail(msg):
    print(f"{RED}FAIL{RESET} {msg}")
    sys.exit(1)


def hash_file(path):
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def main():  # noqa: PLR0912, PLR0915
    print(f"{BOLD}🛡️  COUNCIL READINESS PROOF PROTOCOL 🛡️{RESET}")
    print("=" * 60)

    dist_dir = repo_root / "dist"

    # 1. Artifact Existence
    print(f"\n{BOLD}[1] Artifact Inventory{RESET}")
    drop_zip = list(dist_dir.glob("TRADER_OPS_READY_TO_DROP_v*.zip"))
    code_zip = list(dist_dir.glob("TRADER_OPS_CODE_v*.zip"))

    if not drop_zip:
        print_fail("Versioned Drop Zip not found")
    if not code_zip:
        print_fail("Code Zip not found")

    drop_zip = sorted(drop_zip, key=version_key)[-1]
    code_zip = sorted(code_zip, key=version_key)[-1]
    print_pass(f"Found Artifacts: {drop_zip.name}")

    # 2. Bit-Perfect Identity
    print(f"\n{BOLD}[2] Identity Sovereignty{RESET}")
    drop_hash = hash_file(drop_zip)

    print(f"    Hash: {drop_hash}")

    # 3. Sidecar Verification
    print(f"\n{BOLD}[3] Consumer Verification (Sidecar){RESET}")
    # Prefer versioned sidecar (anti-timeline poison), then .zip.sha256, then legacy unversioned file
    m = re.search(r"v(\d+\.\d+\.\d+)", drop_zip.name)
    ver = m.group(1) if m else None
    candidates = []
    if ver:
        candidates.append(dist_dir / f"DROP_PACKET_SHA256_v{ver}.txt")
    candidates.append(dist_dir / (drop_zip.name + ".sha256"))
    candidates.append(dist_dir / "DROP_PACKET_SHA256.txt")
    sidecar = next((p for p in candidates if p.exists()), None)
    if sidecar is None:
        print_fail("Sidecar missing")

    content = sidecar.read_text().strip()
    if drop_hash not in content:
        print_fail(f"Sidecar ({sidecar.name}) does not contain correct hash")
    print_pass(f"Sidecar ({sidecar.name}) contains valid Drop Hash")

    # 4. Code Hash Binding
    print(f"\n{BOLD}[4] Metadata Binding (The Golden Thread){RESET}")
    metadata_path = repo_root / "reports/forge/synthetic_smoke/RUN_METADATA.json"
    if not metadata_path.exists():
        print_fail("RUN_METADATA.json missing (Did you run make all?)")

    with open(metadata_path) as f:
        meta = json.load(f)

    real_code_hash = hash_file(code_zip)
    meta_code_hash = meta.get("code_hash")

    if real_code_hash != meta_code_hash:
        print_fail(f"Metadata lies! Claims: {meta_code_hash[:8]}... Real: {real_code_hash[:8]}...")
    print_pass(f"RUN_METADATA binds truthfully to Code Zip ({real_code_hash[:8]}...)")

    # 5. Manifest Canon (Institutional Gold Check)
    print(f"\n{BOLD}[5] Manifest Integrity (Council Canon){RESET}")
    canon_verified = False
    with zipfile.ZipFile(code_zip, "r") as zf:
        try:
            # 5a. Get Manifest Hash
            manifest_bytes = zf.read("docs/ready_to_drop/PAYLOAD_MANIFEST.json")
            manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
            
            # 5b. Check Canon (Historical Note: previously checked for circularity)
            # files = manifest.get("file_sha256", {})
            # if "docs/ready_to_drop/COUNCIL_CANON.yaml" in files:
            #     print_fail("COUNCIL_CANON.yaml found in Manifest (Circular Dependency Detected!)")
            
            # 5c. Verify Canon Fingerprint
            canon_bytes = zf.read("docs/ready_to_drop/COUNCIL_CANON.yaml")
            canon_txt = canon_bytes.decode("utf-8")
            m = re.search(r'fingerprint_sha256:\s*"([a-f0-9]+)"', canon_txt)
            if not m:
                print_fail("COUNCIL_CANON.yaml missing fingerprint_sha256 field")
            
            if m.group(1) == manifest_hash:
                canon_verified = True
            else:
                print_fail(f"Canon Fingerprint ({m.group(1)[:8]}) != Manifest Hash ({manifest_hash[:8]})")
                
        except KeyError as e:
            print_fail(f"Missing Critical File: {e}")

    if not canon_verified:
        print_fail("COUNCIL_CANON.yaml validation failed")
    print_pass("COUNCIL_CANON.yaml truthfully binds the Manifest Fingerprint (Gold Chain)")

    # 6. Physics Verification
    print(f"\n{BOLD}[6] Physics Verification (Split-Brain Check){RESET}")
    eq_periods = infer_periods_per_year("1d", is_crypto=False)
    crypto_periods = infer_periods_per_year("1d", is_crypto=True)

    if eq_periods == 252 and crypto_periods == 365:  # noqa: PLR2004
        print_pass(f"Time Physics Correct: Equities={eq_periods}, Crypto={crypto_periods}")
    else:
        print_fail(f"Time Physics Broken! Eq={eq_periods}, Crypto={crypto_periods}")

    print("\n" + "=" * 60)
    print(f"{BOLD}{GREEN}✅ PROOF COMPLETE: SYSTEM IS COUNCIL READY{RESET}")
    print("=" * 60)


if __name__ == "__main__":
    main()
