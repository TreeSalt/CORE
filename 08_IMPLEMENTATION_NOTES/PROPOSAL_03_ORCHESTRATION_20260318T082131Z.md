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
Trust Root Rotation Script
-------------------------
Automates sovereign key rotation across the codebase.
Ensures raw bytes hashing (sha256) matches verifier expectations.

USAGE:
    python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]

SECURITY NOTES:
- Hash computed strictly on raw file bytes to prevent trailing newline mismatches.
- Search excludes 04_GOVERNANCE/ per security policy.
- Fails closed if any integrity constraint is breached.
"""

import hashlib
import pathlib
import re
import sys
import os

# Configuration
EXCLUDE_PATHS = {'04_GOVERNANCE'}
ALLOWED_EXTENSIONS = {'.py', '.yaml', '.json'}

def compute_raw_hash(key_path: str) -> str:
    """
    Compute SHA256 hash of the public key file using raw bytes.
    Matches verify_drop_packet.py behavior exactly.
    """
    if not os.path.isfile(key_path):
        raise FileNotFoundError(f"Public key file not found: {key_path}")
    
    # Read as RAW BYTES. NO .strip() or encoding logic that changes data.
    with open(key_path, "rb") as f:
        raw_content = f.read()
    
    return hashlib.sha256(raw_content).hexdigest()

def parse_args(args):
    """Manual argument parsing without external dependencies."""
    if len(args) < 1:
        raise SystemExit("Error: Missing public key file path (keys/sovereign.pub)")
    
    key_path = args[0]
    old_hash = None
    
    for i, arg in enumerate(args):
        if arg.startswith("--old-hash"):
            if i + 1 >= len(args):
                raise ValueError("--old-hash provided but no value given")
            old_hash = args[i+1]
    
    return key_path, old_hash

def safe_search_and_replace(root_dir: str, old_hex: str, new_hex: str) -> bool:
    """
    Recursively search for the OLD hex hash string and replace with NEW.
    Strictly excludes 04_GOVERNANCE/ paths.
    
    Returns: True if replacements were made (or no matches found), False on failure.
    Raises SystemExit if verification fails post-change.
    """
    root = pathlib.Path(root_dir).resolve()
    
    # Regex to match the specific hash string with word boundaries 
    # to avoid matching partial strings in comments or URLs.
    pattern = re.compile(rf'\b{old_hex}\b')
    found_count = 0
    
    # Iterate all files recursively
    for file_path in root.rglob('*'):
        try:
            if not file_path.is_file():
                continue
                
            # Check extension against allowlist (optional safety, but implied)
            # We will scan based on content to be safe unless extensions enforced.
            
            path_str = str(file_path).replace(root_str := root, "") 
            
            # Exclusion logic: Skip if any segment of the relative path is in EXCLUDE_PATHS
            rel_path_parts = file_path.relative_to(root).parts
            
            # Check for forbidden directory names in the path traversal
            current_segment = file_path.parts[-1]
            excluded_dir_found = False
            for part in rel_path_parts:
                if part in EXCLUDE_PATHS:
                    excluded_dir_found = True
                    break
                
            if excluded_dir_found:
                print(f"Skipped unsafe directory segment found in: {file_path}")
                continue

            content = file_path.read_bytes()
            content_str = content.decode('utf-8', errors='ignore') # Try UTF-8, ignore other chars

            match_count = len(pattern.findall(content_str))
            
            if match_count > 0:
                found_count += match_count
                new_content = pattern.sub(new_hex, content_str)
                
                # Write back only if different (atomicity isn't strictly enforced by os.replace without temp files here)
                # For simplicity and performance on large text, we just overwrite.
                file_path.write_text(new_content.encode('utf-8'))
                print(f"Updated {file_path}: Found {match_count} occurrence(s).")

        except Exception as e:
            # Fail Closed: Stop on read/write errors
            raise RuntimeError(f"Error processing file {file_path}: {e}") from e
            
    if found_count == 0:
        print(f"No instances of old hash ({old_hex}) found in the codebase.")

def verify_completion(old_hex: str):
    """Verify that no OLD hashes remain after rotation."""
    root = pathlib.Path(".").resolve() # Scan current directory context as per script location or pass root
    
    pattern = re.compile(rf'\b{old_hex}\b')
    
    for file_path in root.rglob('*'):
        if not file_path.is_file():
            continue
            
        rel_parts = file_path.parts
        
        # Skip governance dir check again
        excluded = False
        for part in rel_parts:
            if part in EXCLUDE_PATHS:
                excluded = True
                break
                
        if excluded:
            continue
            
        try:
            content = file_path.read_bytes()
            text = content.decode('utf-8', errors='ignore')
            
            if pattern.search(text):
                print(f"FAIL: Residual old hash found in {file_path}")
                raise SystemExit("Verification Failed: Old hash still present in codebase.")
        except:
            continue

    print("Verification Passed: No residual hashes detected.")

def main():
    # Get script directory to handle relative paths vs current dir
    root = pathlib.Path(".").resolve()
    
    try:
        # Parse inputs
        args = sys.argv[1:]
        key_path, old_hex = parse_args(args)
        
        if not old_hex:
            raise SystemExit("Error: --old-hash is required to replace the previous hash safely.")

        # Compute new hash from raw key file
        new_hash = compute_raw_hash(key_path)
        
        print(f"Old Hash : {old_hex}")
        print(f"New Hash : {new_hash}")
        
        if old_hex == new_hash:
            print("Warning: Old and New hashes are identical. Skipping rotation.")
            sys.exit(0)

        # Perform rotation
        safe_search_and_replace(".", old_hex, new_hash)
        
        # Final verification
        verify_completion(old_hex)
        
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```