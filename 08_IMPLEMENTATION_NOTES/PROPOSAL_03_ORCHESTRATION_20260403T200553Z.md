---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from pathlib import Path

path = Path("COUNCIL_CANON.yaml")

if not path.exists():
    print(f"File {path} not found.")
else:
    content = path.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    seen = set()
    unique_lines = []
    
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
            
    result = '\n'.join(unique_lines)
    
    # Preserve trailing newline if it existed
    if content.endswith('\n'):
        result += '\n'
        
    path.write_text(result, encoding='utf-8')

print("Deduplication complete.")<|endoftext|><|im_start|>user
你是一名专业的前端开发工程师。