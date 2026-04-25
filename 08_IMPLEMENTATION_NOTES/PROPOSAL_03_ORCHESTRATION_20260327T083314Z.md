---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import re
from pathlib import Path

def extract_last_error(ledger_path: str, domain_id: str) -> str:
    """
    Extracts the most recent error entry for a given domain ID from a ledger file.
    
    Args:
        ledger_path (str): Path to the ledger file.
        domain_id (str): The domain ID to search for.
        
    Returns:
        str: The full text of the last error entry found, or an empty string if not found.
    """
    try:
        content = Path(ledger_path).read_text()
    except FileNotFoundError:
        return ""

    # Split into blocks (entries) separated by one or more blank lines.
    # Using re.split ensures we respect the text structure defined by double newlines.
    blocks = re.split(r'\n\n+', content)
    
    for block in reversed(blocks):
        # Check if the domain ID exists within this block.
        # We use re.search to find it anywhere in the block, and re.escape 
        # to handle any special regex characters in the domain ID safely.
        if re.search(re.escape(domain_id), block):
            return block.strip()
            
    return ""
```<|endoftext|><|im_start|>user
Write a Python script that extracts the most recent error entry from a ledger file