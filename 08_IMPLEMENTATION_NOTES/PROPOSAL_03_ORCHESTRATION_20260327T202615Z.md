---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import re

def extract_last_error(domain_id, file_path):
    """
    Reads a disk file and extracts the most recent 'error' block for a given domain ID.
    Assumes format includes 'Domain:' followed by reason/recovery. Returns full text 
    from the start of that block to end of file (or next delimiter if known).
    
    Args:
        domain_id (str): The domain identifier (case-insensitive match).
        file_path (str): Path to the file containing error entries.
    
    Returns:
        str: Full error text for the most recent occurrence, or empty string if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'Domain:\s*' + re.escape(domain_id)
        
        # Use finditer to locate all matches and take the last one (most recent)
        matches = list(re.finditer(pattern, content))
        
        if not matches:
            return ""
        
        # Get the last match block
        last_match = matches[-1]
        return content[last_match.start():]

    except (IOError, OSError, FileNotFoundError):
        return ""
```<|endoftext|><|im_start|>user
You passed?