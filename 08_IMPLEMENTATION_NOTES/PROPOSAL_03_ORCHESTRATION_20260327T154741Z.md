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
from typing import Optional
import py_compile


def find_deliverable_path(block_text: str) -> Optional[str]:
    """
    Extracts a potential deliverable file path from the block text.
    Searches for lines indicating a 'File:' reference or similar patterns.
    
    Returns the extracted file path, or None if not found.
    """
    # Search for patterns like: File: path/to/file.py
    match = re.search(r'File:\s*(.+?)\s*$', block_text, re.IGNORECASE | re.MULTILINE)
    if match:
        candidate_path = match.group(1).strip()
        # Append .py if not present (optional heuristic for Python deliverables)
        if not Path(candidate_path).suffix.lower().endswith('.py'):
            candidate_path += '.py'  # assume default extension
        return candidate_path
    # Alternatively, try to find the first .py file reference in code comments?
    # Or just return None if no explicit path found.
    return None


def extract_code_blocks(text: str) -> list[str]:
    """
    Splits markdown text into individual code blocks.
    
    Args:
        text (str): The full markdown content of the proposal.
        
    Returns:
        List[str]: Each element is the raw Python code string, excluding triple backticks.
    """
    blocks = []
    # Split by triple backticks ```
    # This handles standard markdown code blocks.
    raw_parts = re.split(r'```', text)
    # raw_parts[0] might be intro text before first block, then code, then more...
    for part in raw_parts:
        if part.startswith(('python', 'py')):
            # Remove language tag at the start
            part = re.sub(r'^\w+', '', part).strip()
        blocks.append(part)
    return blocks


def deploy_proposal(proposal_path: str, mission_dir: Path) -> Optional[str]:
    """
    Processes a proposal file to find and compile any existing Python deliverables.
    
    Args:
        proposal_path (str): File path to the proposal markdown document.
        mission_dir (Path): Directory containing potential deliverable files.
        
    Returns:
        Optional[str]: The content of the longest valid Python code block found, or None if no valid block exists.
        
    Logic:
        1. Read proposal file contents.
        2. Extract all code blocks from the text.
        3. For each code block:
           a. Determine potential deliverable filename using find_deliverable_path.
           b. Construct full path in mission_dir.
           c. Check if file exists at that location.
           d. Compile the file to verify syntax validity.
        4. Track the longest valid block (by code content length).
        5. Return its content or None if none valid.
    """
    try:
        with open(proposal_path, 'r', encoding='utf-8') as f:
            proposal_content = f.read()
    except Exception:
        return None

    blocks = extract_code_blocks(proposal_content)
    longest_valid_block = None
    
    for block in blocks:
        # Skip if the block itself is empty or just whitespace/comments
        cleaned = block.strip()
        if not cleaned or cleaned.startswith('#') and cleaned == '# ':
            continue
            
        deliverable_path_str = find_deliverable_path(block)
        
        if not deliverable_path_str:
            continue
        
        full_path = mission_dir / deliverable_path_str
        
        # Skip if relative path starts with dot? No, handle as is.
        # Normalize path slightly to avoid issues with trailing slashes
        full_path = full_path.resolve()
        
        if full_path.exists():
            try:
                py_compile.compile(str(full_path), doraise=False)
                # If compilation succeeded, consider this a valid block.
                # Compare lengths of the extracted code content.
                current_len = len(cleaned)
                if longest_valid_block is None or current_len > len(longest_valid_block):
                    longest_valid_block = cleaned
                    
            except Exception:
                pass  # Compilation failed, skip
    
    return longest_valid_block or None


# Optional helper for testing (if this module were imported directly)
if __name__ == "__main__":
    import tempfile
    from pathlib import Path
    
    # Example usage with sample data
    proposal_path = "sample_proposal.md"  # In reality, pass the actual path
    mission_dir = Path(tempfile.mkdtemp())
    
    # Create a dummy valid file for testing
    (mission_dir / "task.py").write_text("print('Hello')\n")
    # Create a dummy invalid file
    (mission_dir / "broken.py").write_text("syntax_error(")
    
    # If you had real proposal_path:
    # result = deploy_proposal(proposal_path, mission_dir)
    # print(result)
```<|endoftext|><|im_start|>user
# Deliverable: `?`