---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
#!/usr/bin/env python3
"""
scripts/rotate_trust_root.py

Mission: Automates sovereign key rotation across the entire codebase.
Security Class: INTERNAL
Domain: 03_ORCHESTRATION

Usage: python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]

CRITICAL SECURITY NOTE:
    - Hash computation must match verify_drop_packet.py exactly.
    - Raw bytes read from file (no strip).
    - Fail closed if verification fails.
"""

import hashlib
import pathlib
import sys
import os

# Constants
FORBIDDEN_DIRECTORIES = {'04_GOVERNANCE'}
ALLOWED_EXTENSIONS = {'.py', '.yaml', '.json', '.yml'}

def compute_public_key_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of the public key file.
    
    CRITICAL SECURITY NOTE: 
    Must read as raw bytes to match verifier logic exactly.
    Do NOT strip whitespace or newline before hashing.
    """
    path = pathlib.Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Public key file not found: {file_path}")
    
    # Read exactly as verifier does: open(path, "rb").read()
    raw_bytes = path.read_bytes() 
    
    # Compute hash of raw bytes
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
    
    return sha256_hash

def find_config_files(root_dir: pathlib.Path) -> list[pathlib.Path]:
    """Recursively find Python, YAML, JSON files excluding forbidden dirs."""
    config_files = []
    if not root_dir.exists():
        return config_files
    
    # Walk directory tree
    for current_path in root_dir.rglob('*'):
        if current_path.is_file() and current_path.suffix.lower() in ALLOWED_EXTENSIONS:
            # Check path string to avoid forbidden dirs
            rel_path = str(current_path)
            # Filter out contents of forbidden directories
            if any(ford in rel_path for ford in FORBIDDEN_DIRECTORIES):
                continue
            config_files.append(current_path)
            
    return config_files

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]")
        sys.exit(1)
    
    public_key_path = sys.argv[1]
    
    # Parse optional args
    old_hash = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--old-hash':
            if i + 1 >= len(sys.argv):
                print("Error: --old-hash requires a value")
                sys.exit(1)
            old_hash = sys.argv[i+1]
            i += 2
        else:
            i += 1
            
    # Step 1: Compute New Hash from raw bytes
    try:
        new_hash_raw = compute_public_key_hash(public_key_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    # Validate hash format (64 hex chars)
    if len(new_hash_raw) != 64 or not all(c in '0123456789abcdef' for c in new_hash_raw):
        print(f"Error: Computed hash length/format invalid. {new_hash_raw}")
        sys.exit(1)

    # Step 2: Validate Old Hash provided
    if old_hash is None:
        print("Error: Must provide --old-hash to perform rotation.")
        sys.exit(1)
        
    # Normalize hex for comparison (lowercase to be safe)
    old_hash_normalized = old_hash.lower()
    new_hash_normalized = new_hash_raw.lower()
    
    # Check if valid old hash provided
    if len(old_hash_normalized) != 64 or not all(c in '0123456789abcdef' for c in old_hash_normalized):
        print(f"Error: Invalid --old-hash format.")
        sys.exit(1)

    # Step 3: Locate and Replace
    changed_count = 0
    affected_files = []
    
    try:
        files_to_update = find_config_files(pathlib.Path('.'))
        
        for f_path in files_to_update:
            try:
                original_content_str = f_path.read_bytes().decode('utf-8', errors='ignore')
                
                if old_hash_normalized in original_content_str:
                    # Only update if actually found and replace is valid
                    updated_content_str = original_content_str.replace(old_hash_normalized, new_hash_normalized)
                    
                    # Write back safely
                    f_path.write_text(updated_content_str, encoding='utf-8')
                    changed_count += 1
                    affected_files.append(f_path.name)
                    
            except Exception as e:
                print(f"Error reading/writing {f_path}: {e}")
        
        if changed_count == 0:
            # No changes needed or errors occurred
            print("No files containing the old hash were found.")
            
    except SystemExit:
        raise
        
    # Step 4: Verification
    # Search again to ensure no old hashes remain
    remaining_old_hashes = 0
    
    for f_path in find_config_files(pathlib.Path('.')):
        try:
            content_str = f_path.read_bytes().decode('utf-8', errors='ignore')
            if old_hash_normalized in content_str:
                remaining_old_hashes += 1
                
        except Exception:
            pass
            
    if remaining_old_hashes > 0:
        print(f"ERROR: {remaining_old_hashes} instances of the old hash remain in codebase.")
        sys.exit(1)

    # Success
    print(f"Successfully rotated trust root. Updated {changed_count} files (e.g., {', '.join(affected_files)}).")
    sys.exit(0)

if __name__ == '__main__':
    main()
```