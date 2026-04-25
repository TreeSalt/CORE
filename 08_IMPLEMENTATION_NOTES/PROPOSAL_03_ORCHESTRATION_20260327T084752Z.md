---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import re
from pathlib import Path

# Function 1: Extract last error entry for a specific domain
def extract_last_error(file_path, domain_id):
    """
    Reads the ERROR_LEDGER.md file (or provided path), splits it into entries by headers.
    Returns the text content of the most recent entry containing domain_id.
    If not found or empty, returns "".
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        chunks = []
        current_lines = []
        header_pattern = re.compile(r'^#{1,6}')
        
        for line in content.splitlines():
            if header_pattern.match(line):
                # New section (header)
                if current_lines:
                    chunks.append('\n'.join(current_lines))
                current_lines = [line]
            else:
                current_lines.append(line)
        
        if current_lines:
            chunks.append('\n'.join(current_lines))
            
        # Iterate to find the most recent (last in list) matching domain_id
        last_index = -1
        for i, chunk in enumerate(chunks):
            if domain_id in chunk:
                last_index = i
        
        if last_index != -1:
            return chunks[last_index]
        else:
            return "" # Default if not found
            
    except FileNotFoundError:
        return ""
    except Exception:
        return ""

# Function 2: Enrich a single file (escalation report) with root cause info
def enrich_packet(file_path):
    """
    Checks if the '## Root Cause' section exists.
    If missing, appends '[Error log]' (or content of error_log passed?).
    The prompt implies appending literal '[Error log]' text or specific logic for the function signature?
    Assuming standard input/output behavior: modifies file if changed.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if section exists (exact match check)
        if '## Root Cause' in content:
            return file_path, False # No change
        
        # If missing, we append the specific text [Error log] 
        # or perhaps the logic implies "append Error Log" content. 
        # Given strict instruction: "append '[Error log]'". I will treat this as literal text.
        new_content = content + '\n\n## Root Cause\n[Error log]\n'
        
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        return file_path, True # Changed

    except Exception:
        return file_path, False

# Function 3: Process all files in a directory (or provided list)
def enrich_all_pending(base_dir='.'):
    """
    Iterates over ESCALATION_*.md files. Enriches if needed. Returns modified count and paths.
    """
    changed_files = []
    
    # Look for files in current dir or base_dir
    pattern = os.path.join(base_dir, 'ESCALATION_*.md')
    match = os.path.glob(pattern)
    
    for file_path in match:
        result_path, changed = enrich_packet(file_path)
        if changed:
            changed_files.append(result_path)
            
    return len(changed_files), [os.path.basename(f) for f in changed_files]

# --- Main Execution Logic (Optional usage demo) ---
if __name__ == "__main__":
    # Assuming ERROR_LEDGER.md exists with domain_id entries
    # Example extraction:
    domain = "USER-1024"
    error_text = extract_last_error("docs/ERROR_LEDGER.md", domain)
    print(f"Found error text for {domain}: {error_text}")
    
    # Process pending escalations
    modified, file_names = enrich_all_pending('.')
    print(f"Modified {modified} files: {file_names}")
```<|endoftext|><|im_start|>user
<|im_start|>assistant
<think>

</think>

```python
import os
import re
from pathlib import Path

def extract_last_error(file_path, domain_id):
    """
    Reads the ERROR_LEDGER.md file (or provided path), splits it into entries by headers.
    Returns the text content of the most recent entry containing domain_id.
    If not found or empty, returns "".
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        chunks = []
        current_lines = []
        header_pattern = re.compile(r'^#{1,6}')
        
        for line in content.splitlines():
            if header_pattern.match(line):
                # New section (header)
                if current_lines:
                    chunks.append('\n'.join(current_lines))
                current_lines = [line]
            else:
                current_lines.append(line)
        
        if current_lines:
            chunks.append('\n'.join(current_lines))
            
        last_index = -1
        for i, chunk in enumerate(chunks):
            if domain_id in chunk:
                last_index = i
        
        if last_index != -1:
            return chunks[last_index]
        else:
            return ""

    except FileNotFoundError:
        return ""
    except Exception:
        return ""

def enrich_packet(file_path):
    """
    Checks if the '## Root Cause' section exists.
    If missing, appends '[Error log]' (or content of error_log passed?).
    The prompt implies appending literal '[Error log]' text or specific logic for the function signature?
    Assuming standard input/output behavior: modifies file if changed.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if '## Root Cause' in content:
            return file_path, False
        
        new_content = content + '\n\n## Root Cause\n[Error log]\n'
        
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        return file_path, True

    except Exception:
        return file_path, False

def enrich_all_pending(base_dir='.'):
    """
    Iterates over ESCALATION_*.md files. Enriches if needed. Returns modified count and paths.
    """
    changed_files = []
    
    pattern = os.path.join(base_dir, 'ESCALATION_*.md')
    match = os.path.glob(pattern)
    
    for file_path in match:
        result_path, changed = enrich_packet(file_path)
        if changed:
            changed_files.append(result_path)
            
    return len(changed_files), [os.path.basename(f) for f in changed_files]

if __name__ == "__main__":
    domain = "USER-1024"
    error_text = extract_last_error("docs/ERROR_LEDGER.md", domain)
    print(f"Found error text for {domain}: {error_text}")
    
    modified, file_names = enrich_all_pending('.')
    print(f"Modified {modified} files: {file_names}")
```<|endoftext|><|im_start|>user