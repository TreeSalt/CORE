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
Deploy Ratified Proposals to Target Locations.
Scan 08_IMPLEMENTATION_NOTES for ratified markdown proposals and deploy their code.
Domain: 03_ORCHESTRATION
Output filename: scripts/deploy_proposals.py
"""

import re
import sys
import argparse
from pathlib import Path

# Constants defined by Domain constraints
SOURCE_DIR = "08_IMPLEMENTATION_NOTES"
FORBIDDEN_PATH_PREFIX = "04_GOVERNANCE/"
DEFAULT_OUTPUT_FILE = "scripts/deploy_proposals.py"

def main():
    parser = argparse.ArgumentParser(description="Deploy ratified proposals")
    # Allow overriding source directory for testing, default to defined constant
    parser.add_argument("--source", default=SOURCE_DIR, help=f"Source directory (default: {SOURCE_DIR})")
    args = parser.parse_args()

    base_source_path = Path(args.source)

    # FATAL: Source directory must exist
    if not base_source_path.exists():
        print(f"FATAL: Source directory '{base_source_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not base_source_path.is_dir():
        print(f"FATAL: Source path is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Find proposal files
    proposals = list(base_source_path.glob("PROPOSAL_*.md"))
    
    deployed_count = 0
    skipped_count = 0
    
    for md_file in proposals:
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # Requirement Check: Must be RATIFIED
            if "STATUS: RATIFIED" not in content:
                continue 
            
            # Requirement Check: Read OUTPUT line from mission file (proposal)
            out_match = re.search(r'^OUTPUT:\s*(.+)', content, re.MULTILINE)
            if not out_match:
                skipped_count += 1
                continue
            
            raw_path = out_match.group(1).strip()
            
            # Construct full path to target
            # Use Path constructor which handles both relative and absolute strings correctly
            # But we should ensure we don't escape outside the project root or forbidden areas
            try:
                target = Path(raw_path)
                
                # Resolve relative paths relative to the script's current working directory
                if not target.is_absolute():
                    target = (Path.cwd() / target).resolve()

                # FAIL CLOSED: Check forbidden path prefixes
                if FORBIDDEN_PATH_PREFIX in str(target):
                    print(f"FATAL: Attempting to write to forbidden path '{target}'")
                    sys.exit(1)
                
                # Create parent directories
                target.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                 skipped_count += 1
                 continue 
            
            # Extract Code (requirement)
            # Look for standard python code blocks within the proposal markdown
            # We need to handle cases where multiple code blocks might exist, though usually one is expected.
            # Assuming the last or first python block is intended.
            code_blocks = list(re.finditer(r'```(?:python|py)\n(.*?)```', content, re.DOTALL))
            
            if not code_blocks:
                skipped_count += 1
                continue
            
            # Use the most recent python block as the "code"
            code_block_text = code_blocks[-1].group(1)
            # Clean up leading/trailing whitespace within the block
            code = code_block_text.strip()
            
            if not code:
                 skipped_count += 1
                 continue

            # Idempotency Check
            existing_path = target
            if existing_path.exists():
                try:
                    existing_content = existing_path.read_text()
                    # Check for strict equality (excluding whitespace differences if needed, but here let's be exact)
                    if code == existing_content:
                        continue 
                except Exception:
                    # If read fails (corrupt file), we overwrite or fail?
                    # To avoid blocking logic on broken files, we will overwrite.
                    pass
            
            # Deployment Step
            # Overwrite with new content (idempotent check above handles duplicates)
            existing_path.write_text(code)
            deployed_count += 1

        except Exception as e:
            # Log error to stderr and continue processing next file
            print(f"Warning: Error processing {md_file.name}: {e}", file=sys.stderr)

    # Output summary
    total_processed = deployed_count + skipped_count
    print(f"Deployed: {deployed_count}, Skipped (Matched/No-Output): {skipped_count} out of {len(proposals)} proposals processed.")

if __name__ == "__main__":
    main()
```