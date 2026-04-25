---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pytest
import tempfile
from pathlib import Path


def test_extract_code_blocks():
    """Test code block extraction from markdown"""
    md_content = f"""# Test Proposal

This is a sample proposal with some {{content}}.

Here is the python code:

```python
def hello():
    print("Hello World")
```

More text here."""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(md_content)
    temp_file.close()

    result = extract_code_blocks(temp_file.name, {'language': 'python'})
    assert len(result) == 1
    assert 'def hello' in result[0]['content']


def test_find_best_block_picks_longest_valid():
    """Test that longest valid code block is selected"""
    md_content = """# Test

```python
block_1 = 1 + 2

valid block 2
more text here

block_3 = 3 + 4
```
Invalid block syntax!

Another valid:
```javascript
var x = 5;
var y = 6;
```"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(md_content)
    temp_file.close()

    blocks = find_best_block(temp_file.name, {'language': 'python'})
    assert len(blocks) == 2
    # Should pick the longest valid python block
    for block in blocks:
        assert block['language'] == 'python'


def test_find_deliverable_from_proposal():
    """Test File: line parsing works"""
    md_content = """Proposal for file changes:

File: my_file.txt, action: create, content: hello world

Another section with File: config.json, action: update"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(md_content)
    temp_file.close()

    deliverables = find_deliverable(temp_file.name)
    assert len(deliverables) == 2
    for deliverable in deliverables:
        assert 'file_path' in deliverable
        assert 'action' in deliverable


def test_dry_run_no_write():
    """Test deploy with dry_run does not create files"""
    md_content = """# Test Proposal

File: new_file.txt, action: create, content: test data"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(md_content)
    temp_file.close()

    deploy(temp_file.name, {'dry_run': True})

    # Verify file was not created at project root
    assert Path('new_file.txt').exists() is False


def extract_code_blocks(markdown_path: str, language_filter: dict):
    """Extract code blocks from markdown"""
    with open(markdown_path) as f:
        content = f.read()

    extracted = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if '```' in line:
            language_start = True
            code_lines = []
            for j in range(i + 1, len(lines)):
                if '```' not in lines[j]:
                    code_lines.append(lines[j])
                else:
                    break
            extracted.append({'language': language_filter.get('language', ''), 'content': '\n'.join(code_lines)})
        i += 1

    return extracted


def find_best_block(markdown_path: str, filters):
    """Find best code block from markdown"""
    blocks = extract_code_blocks(markdown_path, filters)
    valid_blocks = [b for b in blocks if b['language'] not in ('', 'text')]
    return sorted(valid_blocks, key=lambda x: len(x['content']), reverse=True)[:1]


def find_deliverable(markdown_path: str):
    """Find deliverables from proposal markdown"""
    deliverables = []

    with open(markdown_path) as f:
        content = f.read()

    lines = content.split('\n')
    for line in lines:
        if 'File:' in line and ',' in line:
            parts = line.split(',')
            file_path = parts[0].replace('File:', '').strip().lower()
            action = parts[1].split(':')[0].strip()
            deliverables.append({'file_path': file_path, 'action': action})

    return deliverables


def deploy(markdown_path: str, options):
    """Deploy changes from markdown"""
    if not options.get('dry_run', False):
        deliverables = find_deliverable(markdown_path)
        for d in deliverables:
            Path(d['file_path']).write_text("dummy content")


class CodeBlockExtractor:
    pass
```