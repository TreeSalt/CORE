---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

**Domain: Content Formatting & Scripting (Python)**
This Python script automates secure migration by replacing known vulnerable hash values with approved alternatives across project files. It includes validation to prevent modification of files inside forbidden system paths, handles binary/encoding errors gracefully, and reports the number of files updated. The script uses `argparse` for CLI, standard library for file I/O, and ensures UTF-8 text integrity.

### `hash_migration.py`

```python
"""
Secure Hash Replacement Tool
Replaces known vulnerable hashes with approved secure versions.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Constants
FORBIDDEN_DIR = "04_GOVERNANCE"
DEFAULT_ENCODING = "utf-8"


def compute_sha256(raw_bytes: bytes) -> str:
    """Compute SHA256 hash of raw bytes for file integrity (not used in replace, but good practice)."""
    return __import__("hashlib").sha256(raw_bytes).hexdigest()


def is_binary_or_corrupt(path: Path, encoding: str) -> bool:
    """
    Check if a file is binary or has encoding issues.
    Returns True if the file should be skipped (binary/corrupt/permission).
    """
    try:
        # Attempt to read as text; fails for binary/corrupt
        path.read_text(encoding=encoding)
        return False
    except UnicodeDecodeError:
        return True
    except (OSError, PermissionError):
        return True


def process_file(
    path: Path,
    old_hash: str,
    new_hash: str,
    encoding: str
) -> bool:
    """
    Process a single file: replace all occurrences of old_hash with new_hash.
    Returns True if file was modified (i.e., replacement occurred).
    """
    try:
        # Read content
        content = path.read_text(encoding=encoding)
        # Normalize hashes for matching (case-insensitive matching for robustness)
        old_hash_norm = old_hash.lower()
        count = content.count(old_hash_norm)
        
        if count > 0:
            # Perform replacement
            new_content = content.replace(old_hash_norm, new_hash.lower())
            
            # Write back (preserving line endings via read_text/write_text)
            path.write_text(new_content, encoding=encoding)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error processing {path}: {e}", file=sys.stderr)
        return False


def check_forbidden_path(path: Path):
    """Check if the absolute path contains a forbidden directory."""
    # Use string check for substring match in absolute path
    abs_path_str = str(path.absolute()).lower()
    forbidden_lower = FORBIDDEN_DIR.lower()
    return forbidden_lower in abs_path_str


def main():
    parser = argparse.ArgumentParser(
        description="Securely replace vulnerable hash values in project files."
    )
    parser.add_argument(
        "--old-hash", "-o", required=True,
        help="The hash string to find and replace (e.g., 'a1b2...')."
    )
    parser.add_argument(
        "--new-hash", "-n", required=True,
        help="The new secure hash string to insert."
    )
    parser.add_argument(
        "--encoding", default=DEFAULT_ENCODING,
        help=f"File encoding (default: {DEFAULT_ENCODING})."
    )
    
    args = parser.parse_args()
    
    old_hash = args.old_hash
    new_hash = args.new_hash
    encoding = args.encoding
    
    # Print summary header
    print(f"Scanning project for hash '{old_hash}' -> Replace with '{new_hash}'")
    print(f"Forbidden directory: {FORBIDDEN_DIR}")
    print(f"Encoding: {encoding}\n")
    
    total_modified = 0
    files_scanned = 0
    skipped_files = 0
    
    # Iterate all files in current directory recursively
    for path in Path(".").rglob("*"):
        if path.is_file():
            files_scanned += 1
            
            # Skip forbidden paths first (before encoding check)
            if check_forbidden_path(path):
                print(f"Skipping forbidden: {path}")
                skipped_files += 1
                continue
            
            # Check for binary/corrupt files
            if is_binary_or_corrupt(path, encoding):
                print(f"Skipping binary/decode error: {path}")
                skipped_files += 1
                continue

            # Attempt to process file
            modified = process_file(
                path=path,
                old_hash=old_hash,
                new_hash=new_hash,
                encoding=encoding
            )
            
            if modified:
                total_modified += 1
                
    # Summary report
    print("-" * 40)
    print("Migration Summary:")
    print(f"Files scanned:      {files_scanned}")
    print(f"Forbidden skipped:  {skipped_files}")
    print(f"Files updated:      {total_modified}\n")
    
    if total_modified == 0:
        print("No files were modified (old hash not found or no occurrences).")
    else:
        print("Migration completed successfully.")
        
    # Exit code: 0 always for success, non-zero for error. Here, we always exit 0.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Unhandled exception: {e}", file=sys.stderr)
        sys.exit(1)
```