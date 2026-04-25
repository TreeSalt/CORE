---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the implementation of the `deploy_proposal` function and a corresponding CLI interface based on your requirements. The solution uses only `sys`, `re`, `pathlib`, and `py_compile` for validation, and handles error cases as specified.

```python
import sys
import re
import py_compile
from pathlib import Path

def deploy_proposal(proposal_path: str, mission_dir: str) -> dict:
    """
    Validates a proposal file containing Python code blocks, compiles them, 
    selects the most robust valid block, and deploys it to the specified mission directory.

    :param proposal_path: Path to the proposal file containing code blocks.
    :param mission_dir: Directory where the deployed deliverable will be saved.
    :return: A dictionary with 'status', 'path', or 'error' keys indicating the outcome.
    """
    try:
        prop_file = Path(proposal_path)
        
        # Validation 1: Check proposal file existence and readability
        if not prop_file.exists():
            return {'status': 'ERROR', 'message': f"Proposal file not found: {proposal_path}"}
            
        content = prop_file.read_text(encoding='utf-8')
        
        # Extract code blocks from the proposal (supporting markdown-style blocks)
        # Pattern matches triple backtick-delimited code blocks, common in text proposals
        block_pattern = r'```(?:python|py)?\n([\s\S]*?)\n```'
        blocks = re.findall(block_pattern, content, re.IGNORECASE)
        
        if not blocks:
            return {'status': 'ERROR', 'message': "No code blocks found in proposal"}

        # Extract Python paths for validation
        valid_blocks = []
        error_messages = []

        for i, block_code in enumerate(blocks):
            try:
                # Create a temporary file object to compile the string
                from io import StringIO
                temp_file = StringIO(block_code)
                
                # Try compiling without execution to check syntax/validity
                py_compile.compile(temp_file, doraise=True)
                
                # If compiles successfully, add to valid list
                valid_blocks.append((i, block_code))
            except py_compile.PyCompileError as e:
                error_messages.append(f"Block {i} compilation failed: {str(e)}")

        if not valid_blocks:
            # If no blocks compile, return specific error message as per instructions
            all_errors = '\n'.join(error_messages) if error_messages else "No syntax-valid code block found."
            return {'status': 'ERROR', 'message': f"No deployable code. Details:\n{all_errors}"}

        # Select the most robust block (first valid one, assuming simplicity is robust)
        # If multiple valid, we pick the first encountered to avoid ambiguity unless specified.
        selected_code = valid_blocks[0][1]

        # Determine output filename:
        # 1. Try to extract from comment in the code block itself
        filename = None
        # Look for pattern like `# filename="..."` inside the selected block
        file_name_match = re.search(r'#\s+filename\s*=\s*"([^"]*)"', selected_code)
        if file_name_match:
            filename = file_name_match.group(1)
        
        # 2. Fallback to proposal stem (without extension) or default name
        if not filename:
            # Proposal stem as base
            proposed_name = prop_file.stem
        
        # If mission_dir is empty string, use '.'
        dir_path = Path(mission_dir) if mission_dir else Path('.')
        
        # Construct full path
        deliverable_path = dir_path / f"{proposed_name}.py"

        try:
            # Write the selected block to the file
            deliverable_path.write_text(selected_code, encoding='utf-8')
        except Exception as e:
            return {'status': 'ERROR', 'message': f"Failed to write deliverable file: {str(e)}"}

        return {'status': 'SUCCESS', 'path': str(deliverable_path), 'filename': proposed_name}
        
    except FileNotFoundError:
        return {'status': 'ERROR', 'message': "File not found or read error."}
    except Exception as e:
        return {'status': 'ERROR', 'message': f"Unexpected error: {str(e)}"}

# Main CLI Interface logic
if __name__ == '__main__':
    args = sys.argv[1:]
    
    if len(args) < 2:
        print("Usage: python script.py <proposal_path> [mission_dir]")
        print("If mission_dir is omitted, uses current working directory.")
        print("The proposal file must contain markdown-formatted code blocks.")
        sys.exit(1)

    # Validate arguments just in case (though main checks length)
    prop_file = args[0]
    mission_directory = args[1] if len(args) > 1 else None  # Optional: default to cwd handled inside function
    
    result = deploy_proposal(prop_file, mission_directory)
    
    # Pretty print result for CLI user
    import json
    print(json.dumps(result, indent=2))

```