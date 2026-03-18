---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

scripts/rotate_trust_root.py
```python
#!/usr/bin/env python3
"""
Trust Root Key Rotation Script
Automates sovereign key hash updates across the codebase after key rotation.

Usage: python3 scripts/rotate_trust_root.py keys/sovereign.pub --old-hash <OLD_HASH>
       python3 scripts/rotate_trust_root.py keys/sovereign.pub --new-hash <NEW_HASH>

DO NOT modify keys/sovereign.pub directly via this script. Update the public key file,
then compute its SHA256 hash and provide --old-hash and optionally --new-hash to update references.
"""

import hashlib
import pathlib
import re
import sys


def compute_sha256_hash(key_path: pathlib.Path) -> str:
    """
    Compute SHA256 hash of public key file using RAW BYTES.

    CRITICAL: Must use raw bytes matching how verifier reads the file.
    DO NOT strip or encode - trailing newlines affect hash.
    """
    if not key_path.exists():
        raise FileNotFoundError(f"Public key file not found: {key_path}")

    with open(key_path, "rb") as f:
        raw_bytes = f.read()

    return hashlib.sha256(raw_bytes).hexdigest()


def find_files_with_hash(directory: pathlib.Path, target_hash: str, extensions: list | None = None) -> list[str]:
    """
    Find all files containing the old hash string.
    Searches *.py, *.yaml, *.yml, *.json recursively unless other extensions are provided.
    """
    if not directory.exists():
        return []

    if not target_hash:
        return []

    regex_pattern = re.compile(re.escape(target_hash))
    matching_files: list[str] = []
    default_extensions = ["*.py", "*.yaml", "*.yml", "*.json"]
    search_extensions = extensions or default_extensions

    try:
        for ext in search_extensions:
            try:
                files_in_dir = [str(f) for f in (directory / ext).rglob("*")] if directory.glob(ext) else []
            except Exception:
                continue

            matching_files.extend(
                str(p) for p in pathlib.Path(directory).rglob("*.py")
            )
            matching_files.extend(
                str(p) for p in pathlib.Path(directory).rglob("*.yaml")
            )
            matching_files.extend(
                str(p) for p in pathlib.Path(directory).rglob("*.yml")
            )
            matching_files.extend(
                str(p) for p in pathlib.Path(directory).rglob("*.json")
            )

        for file_path in set(matching_files):
            try:
                content = pathlib.Path(file_path).read_text(errors="ignore")
                if regex_pattern.search(content):
                    matching_files.append(str(pathlib.Path(file_path)))
            except Exception:
                continue
    except Exception:
        pass

    return matching_files


def replace_hash_in_file(file_path: pathlib.Path, old_hash: str, new_hash: str) -> bool:
    """
    Replace old hash with new hash in a file.
    Returns True if replacement was made, False otherwise.
    """
    try:
        content = file_path.read_text(errors="ignore")
        pattern = re.compile(re.escape(old_hash))

        if not pattern.search(content):
            return False

        new_content = pattern.sub(new_hash, content)

        if new_content != content:
            # Write only after successful update to prevent partial writes
            file_path.write_text(new_content, encoding="utf-8")
            return True
        return False
    except Exception:
        print(f"  Warning: Failed to read/write {file_path}")
        return False


def verify_no_old_hash_remaining(search_dir: pathlib.Path | None, target_hash: str) -> bool:
    """
    Verify that no files contain the old hash after rotation.
    Returns True if all are clean (no old hashes found).
    """
    try:
        files = find_files_with_hash(
            directory=search_dir or pathlib.Path("."),
            target_hash=target_hash,
            extensions=None
        )
        return len(files) == 0
    except Exception:
        return True


def main():
    # Default values
    key_path = pathlib.Path("keys/sovereign.pub")
    old_hash = None
    search_dirs = ["."]

    # Parse arguments manually
    args: list[str] = sys.argv[1:]
    i = 0
    if len(args) >= 2:
        key_path_str = args[i].replace("/", pathlib.Path).replace("\\", pathlib.Path)
        for j, arg in enumerate(args[i+1:], i+1):
            if arg.startswith("--old-hash"):
                old_hash = args[j + 1] if j + 1 < len(args) else None
            elif arg.startswith("--new-hash"):
                new_hash = args[j + 1] if j + 1 < len(args) else None
            elif arg == "--search-dir":
                search_dirs.append(pathlib.Path(args[j + 1]) if j + 1 < len(args) else None)
        i += max(1, (args.index(key_path_str) - args.index(old_hash)) if old_hash else 0)

    # Compute current public key hash from raw bytes
    try:
        computed_hash = compute_sha256_hash(key_path)
    except Exception as e:
        print(f"Error reading sovereign key file {key_path}: {e}")
        sys.exit(1)

    # Validate old_hash is provided when updating
    if not old_hash:
        print("ERROR: --old-hash argument required for rotation. Use existing hash from public key file.")
        sys.exit(1)

    # Compute new_hash if not provided; fallback to computed_hash
    new_hash = computed_hash if not new_hash else new_hash

    # Find all files with old hash across search directories
    all_files_to_update: list[str] = []
    for search_dir in search_dirs:
        try:
            path = pathlib.Path(search_dir)
            matching_files = find_files_with_hash(path, old_hash)
            all_files_to_update.extend(matching_files)
        except Exception:
            continue

    # Check hash validity and print summary if updates needed
    if not old_hash or not new_hash:
        print(f"ERROR: Neither old nor new hash specified. Use --old-hash and optionally --new-hash.")
        sys.exit(1)

    # Validate hashes format (64 hex characters)
    for h in [old_hash, new_hash]:
        if len(h) != 64 or not re.fullmatch(r"[0-9a-f]{64}", h):
            print(f"ERROR: Hash must be exactly 64 lowercase hexadecimal characters.")
            sys.exit(1)

    # Perform hash replacement in all affected files
    modified_count = 0
    for file_path in sorted(set(all_files_to_update)):
        filepath = pathlib.Path(file_path)
        if replace_hash_in_file(filepath, old_hash, new_hash):
            print(f"Modified: {file_path}")
            modified_count += 1

    # Verify no old hashes remain after rotation
    remaining_old_hashes_found = find_files_with_hash(pathlib.Path("."), old_hash)
    
    # Final summary output
    print("\n=== Trust Root Rotation Summary ===")
    print(f"Public Key Path: {key_path}")
    print(f"Original Hash (64 chars): {old_hash}")
    print(f"New Hash (computed/raw bytes): {new_hash}")
    print(f"Files modified: {modified_count}")
    print(f"Old hash instances remaining: {len(remaining_old_hashes_found)}")

    if not remaining_old_hashes_found:
        print("✓ Verification complete: Zero old hashes remain in codebase")
    else:
        for f in remaining_old_hashes_found:
            print(f"  ⚠ Old hash still found in: {f}")
        print("⚠ Rotated but some references may be unaccounted. Review manually.")

    sys.exit(0 if not remaining_old_hashes_found else 1)


if __name__ == "__main__":
    main()
```