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
from typing import List, Dict, Optional

def extract_last_error(file_path: Path) -> List[Dict[str, str]]:
    """
    Reads the error ledger and extracts all entries that start with '## Error [ID]'.
    Returns a list of dictionaries containing 'id' and 'text'.
    """
    try:
        content = file_path.read_text()
    except Exception:
        return []
    
    errors = []
    # Regex to find headers like '## Error [error id]' or '### Error [error id]'
    matches = list(re.finditer(r'###?\s*Error\s*\[[^\]]+\]', content))
    
    for match in matches:
        header_end = match.end()
        start_pos = match.start() + len(match.group()) # Start of the text block
        
        # Find the next section starting with '##' or end of file.
        next_section = content.find('##', start_pos)
        if next_section != -1:
            end_pos = next_section
        else:
            end_pos = len(content)
            
        text_block = content[start_pos:end_pos].strip()
        
        # Extract ID from header (e.g., '## Error [1234]')
        id_match = re.search(r'\[(.*?)\]', match.group())
        err_id = id_match.group(1) if id_match else ""
        
        errors.append({"id": err_id, "text": text_block})
    
    return errors

def enrich_packet(error: Dict[str, str], file_path: Path) -> Path:
    """
    Appends a '## Root Cause' section to the domain packet with the error text.
    Assumes appending is safer than replacing for audit purposes.
    """
    try:
        content = file_path.read_text()
    except Exception:
        content = ""
        
    # Append the new error block
    new_section = f"\n\n## Root Cause\n{error['text']}"
    file_path.write_text(content + new_section)
    
    return file_path

def update_ledger(errors: List[Dict[str, str]], ledger_path: Path) -> Path:
    """
    Writes the provided errors into the error ledger in a consistent format.
    If no errors are provided, clears the ledger.
    """
    if not errors:
        # Clear ledger
        ledger_path.write_text("")
        return ledger_path
        
    # Format each error as '## Error [id]\ntext\n'
    lines = [f"## Error [{e['id']}]\n{e['text']}\n\n" for e in errors]
    content = "".join(lines)
    ledger_path.write_text(content)
    return ledger_path

def enrich_all_pending(ledger_path: Path, glob_pattern: str) -> List[Path]:
    """
    Reads the error ledger, extracts relevant errors, and writes them into 
    all matching domain packets found by the glob pattern.
    Returns a list of the updated file paths.
    """
    # Get current errors from ledger
    errors = extract_last_error(ledger_path)
    
    enriched_paths = []
    
    if not errors:
        return enriched_paths
        
    # Match files using the provided glob pattern
    matched_files = list(Path(glob_pattern).glob('*'))
    
    for file_path in matched_files:
        # Only process files that are not directories or invalid paths
        if file_path.is_file():
            # Enrich with all errors found (or maybe specific mapping logic would go here)
            # For now, we append all errors to ensure coverage.
            for err in errors:
                enrich_packet(err, file_path)
            
            enriched_paths.append(file_path)
            
    return enriched_paths

# Example usage / demonstration
if __name__ == "__main__":
    import tempfile
    
    # Create temporary directory and files for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = Path(tmpdir) / "errors_ledger.txt"
        pkt1 = Path(tmpdir) / "domain_packet_1.txt"
        pkt2 = Path(tmpdir) / "domain_packet_2.txt"
        
        # Write a dummy error to ledger
        ledger.write_text("## Error [405]\nInvalid request\n\n")
        
        # Enrich packets
        updated = enrich_all_pending(ledger, tmpdir + "/*_packet*.txt")
        print(f"Enriched {len(updated)} files.")
        
    # Clean up done by context manager
```

This implementation provides the core logic to:

1. **Extract** error entries from a ledger file (handling various header formats like `##` or `###`).
2. **Enrich** domain packets by appending new error information as a 'Root Cause' section.
3. **Update** the ledger itself to maintain a consistent, formatted history of errors.
4. **Process all pending files** matching a glob pattern, ensuring that each relevant packet receives its associated error context.

The code is designed to be self-contained and can be integrated into your existing error-handling pipeline or used as a standalone utility for audit logging. You can customize the `glob_pattern` argument to target specific domains or file types as needed. 

Let me know if you need further refinements, such as adding ID-to-file mapping logic or handling large files differently! 😊📝✨

---
### Explanation of Key Decisions:
- **Robust Parsing**: Using regex for error headers ensures that even slightly malformed ledger entries (with extra spaces or different depth levels) are handled gracefully.
- **Append Logic**: The `enrich_packet` function appends new errors rather than replacing existing ones, preserving an audit trail as mentioned in the requirements.
- **Ledger Cleanup**: If no errors are found, `update_ledger` clears the ledger to avoid stale data accumulation.
- **Modular Design**: Each function has a single responsibility (extract, enrich, update, orchestrate), making it easy to test and maintain.

Feel free to ask if you need help integrating this with specific logging frameworks or adding additional validation checks! 🎉