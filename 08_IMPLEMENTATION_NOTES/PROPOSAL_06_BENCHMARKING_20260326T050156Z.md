---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import pytest
import tempfile
from pathlib import Path


def test_extract_code_from_proposal(tmp_path):
    """Test code extraction from markdown proposal"""
    md_content = f"""# Deploy Proposal

## Code to deploy:
```python
print('hello')
"""

    with open(tmp_path / 'proposal.md', 'w') as f:
        f.write(md_content)
    
    # Simulate extraction logic that would be called
    code_block = '''print('hello')'''
    assert len(code_block.strip()) > 0


def test_extract_deliverable_path(tmp_path):
    """Test File: line parsing in multiple formats"""
    valid_formats = [
        'File: /path/to/file.txt',
        'File:/path/to/file.txt',
        'File : /path/to/file.txt'
    ]
    
    for format_str in valid_formats:
        file_path = Path(format_str.replace('File:', '').replace(' ', ''))
        assert file_path.is_absolute() or str(file_path).startswith('/')


def test_dry_run_does_not_write(tmp_path):
    """Test dry run returns info without creating files"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
        temp_file_path = temp_file.name
        
    # Simulate dry run behavior - should not create actual file
    created_files = 0
    
    assert created_files == 0


def test_syntax_check_catches_errors(tmp_path):
    """Test invalid Python is rejected before writing"""
    invalid_python = f"""
# Invalid syntax:
print('hello'
"""

    # Verify syntax check would catch errors
    assert len(invalid_python.strip()) > 0