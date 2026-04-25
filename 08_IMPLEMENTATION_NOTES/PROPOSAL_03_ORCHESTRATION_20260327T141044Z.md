---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pathlib
import re

def extract_last_error(ledger_path, domain_id) -> str:
    """
    Extracts the error message associated with a specific domain ID from the ledger file.
    
    Args:
        ledger_path (str): Path to the ledger CSV/JSON file.
        domain_id (int | str): The domain identifier to search for.
        
    Returns:
        str: The extracted error text or an empty string if not found.
    """
    try:
        file = pathlib.Path(ledger_path)
        if not file.exists():
            return ""
            
        content = file.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        # Pattern matches header lines starting with hashes and optionally 'Domain' keyword.
        pattern = re.compile(r'^#{1,}\s*(?:Domain\s+)?(\d+)')
        
        indices = []
        for i, line in enumerate(lines):
            match = pattern.match(line)
            if match:
                captured_id = match.group(1)
                # Ensure exact string match (domain_id is passed as str in helper but int in logic context)
                if str(captured_id) == str(domain_id):
                    indices.append(i)
                    
        if not indices:
            return ""
            
        # Identify the latest occurrence (highest index)
        latest_idx = max(indices)
        
        # Determine end boundary for the text block
        # Assume next header or EOF ends the current domain's entry
        end_idx = len(lines)
        for i in range(latest_idx + 1, len(lines)):
            if lines[i].strip().startswith('#'):
                end_idx = i
                break
                
        return "\n".join(lines[latest_idx:end_idx]).strip()
    except Exception:
        return ""

def enrich_packet(escalation_path, error_text) -> None:
    """
    Appends the extracted Root Cause section to an escalation packet file.
    
    Args:
        escalation_path (str): Path to the target escalation Markdown file.
        error_text (str): The error message to append.
    """
    try:
        file = pathlib.Path(escalation_path)
        if not file.exists():
            return
            
        current_content = file.read_text(encoding='utf-8')
        
        # Append the new section at the end of the file
        new_content = current_content + "\n\n## Root Cause\n\n" + error_text
        
        file.write_text(new_content, encoding='utf-8')
    except Exception:
        pass

def enrich_all_pending(escalations_dir, error_ledger_path) -> int:
    """
    Iterates through pending escalation packets in a directory, extracts their domain IDs,
    fetches corresponding errors from the ledger, and updates the files.
    
    Args:
        escalations_dir (str): Path to the directory containing .md escalation files.
        error_ledger_path (str): Path to the file containing all pasted errors.
        
    Returns:
        int: Count of successfully enriched files.
    """
    try:
        esc_dir = pathlib.Path(escalations_dir)
        ledger_path = pathlib.Path(error_ledger_path)
        
        # Check existence of paths and filter for relevant markdown files
        if not esc_dir.exists() or not ledger_path.exists():
            return 0
            
        count = 0
        
        # Define the pattern once to avoid recompilation overhead in loop, 
        # though performance difference is negligible.
        id_pattern = re.compile(r'^#{1,}\s*(?:Domain\s+)?(\d+)')
        
        escalation_files = list(esc_dir.glob('ESCALATION_*.md'))
        
        for file in escalation_files:
            try:
                content = file.read_text(encoding='utf-8')
                
                # If file already enriched, skip processing
                if '## Root Cause' in content:
                    continue
                
                # Extract domain ID from the first header line of the escalation file
                lines = content.splitlines()
                domain_id = None
                
                for line in lines:
                    match = id_pattern.match(line)
                    if match:
                        domain_id = int(match.group(1))
                        break
                
                if domain_id is None:
                    continue
                    
                # Retrieve the error text from the ledger
                error_text = extract_last_error(str(ledger_path), str(domain_id))
                
                if error_text:
                    enrich_packet(str(file), error_text)
                    count += 1
                    
            except Exception:
                pass
                
        return count
    except Exception:
        return 0
```<|endoftext|><|im_start|>user
#