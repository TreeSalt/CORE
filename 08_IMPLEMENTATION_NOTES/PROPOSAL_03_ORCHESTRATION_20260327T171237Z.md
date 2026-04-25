---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import sys
import re

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <proposal_path> <mission_dir>")
        return
    
    proposal_path = sys.argv[1]
    mission_dir = sys.argv[2] # may be used for fallback path logic
    
    try:
        with open(proposal_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Proposal file not found: {proposal_path}")
        return
    
    match = re.search(r'File:[\s]*([^"\n]+)', content) # capture path part
    
    if match:
        raw_path = match.group(1).strip()
        code_path = raw_path.strip('"').strip("'").strip(';', '').strip()
        
        try:
            with open(code_path, 'r') as f:
                code_content = f.read()
            compile(code_content, '<compiled>', 'exec')
            print(f"Compiled successfully: {code_path}")
        except FileNotFoundError:
            print(f"Code file not found: {code_path}")
        except SyntaxError as e:
            print(f"Syntax error in code file:\n{e}")
    else:
        # No 'File:' line -> check corresponding mission file.
        # Extract folder from proposal_path (last part of path)
        if '/' in proposal_path:
            folder = proposal_path.rsplit('/', 1)[0]
        else:
            folder = ""
        
        target_file = f"{folder}.py" if folder else "mission_dir.py"
        
        try:
            with open(target_file, 'r') as f:
                code_content = f.read()
            compile(code_content, '<compiled>', 'exec')
            print(f"Mission file checked and compiled successfully: {target_file}")
        except FileNotFoundError:
            print(f"No corresponding mission file found: {target_file}")
        except SyntaxError as e:
            print(f"Syntax error in mission file:\n{e}")

if __name__ == "__main__":
    main()<|endoftext|><|im_start|>user