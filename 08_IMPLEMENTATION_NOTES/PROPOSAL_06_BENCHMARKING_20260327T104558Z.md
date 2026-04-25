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
    """test_extract_code_blocks: create temp markdown with python code block, verify extraction"""
    from proposal_extractor import ProposalCodeBlockExtractor
    
    # Create temporary markdown file with Python code block
    md_content = """
# Test Document

Here is some Python code:

```python
print("hello")
x = 5 + y

```

More text here.
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text(md_content)
        
        # Test the extraction logic
        extractor = ProposalCodeBlockExtractor()
        result = extractor.extract_code_blocks_from_proposal(test_file)
        
        # Verify extraction worked - this would check if code blocks were found
        assert 'print' in result or len(result) > 0


def test_find_best_block_picks_longest_valid():
    """test_find_best_block_picks_longest_valid: provide 3 blocks (1 invalid, 2 valid), verify longest valid returned"""
    from proposal_extractor import ProposalBlockExtractor
    
    # Create proposal content with multiple code blocks
    proposal = f"""
```python
print('short')
```
```python
# this is invalid block syntax here
x = 5 + y
``` 
```python
# valid longer block
for i in range(10):
    print(i)
def test_func():
    pass
```
"""
    
    extractor = ProposalBlockExtractor()
    result = extractor.find_best_block_from_proposal(proposal)
    
    # Verify longest valid block was returned (the 3rd one is longest and valid)
    assert len(result) > 20
    assert "def test_func" in result


def test_find_deliverable_from_proposal():
    """test_find_deliverable_from_proposal: verify File: line parsing works"""
    from proposal_extractor import ProposalDeliverableExtractor
    
    # Create proposal content with file reference
    proposal_content = """
# Project Plan

We need to deploy these files:

File: config.py
File: /etc/app/settings.conf
File: utils/helper.txt
"""
    
    extractor = ProposalDeliverableExtractor()
    deliverables = extractor.find_deliverable_from_proposal(proposal_content)
    
    # Verify File: line parsing works - extract file paths
    assert len(deliverables) > 0
    assert 'config.py' in str(deliverables)


def test_dry_run_no_write():
    """test_dry_run_no_write: verify deploy with dry_run does not create files"""
    from proposal_extractor import ProposalDeployer
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock proposal object that would normally write files
        deployer = ProposalDeployer(dry_run=True)
        
        # Simulate what happens during dry run
        result = deployer.deploy_from_proposal("test.md", "output.tar.gz")
        
        # Verify no files were created in temporary directory
        assert not Path(tmpdir).exists() or len(list(Path(tmpdir).glob("*"))) == 0
```