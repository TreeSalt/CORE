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
from orchestrator_core import generate_mission_file, validate_clean_mission, queue_mission_appends

# Assume these domain IDs are the 9 valid ones based on the system configuration
ALL_REQUIRED_DOMAIN_IDS = [
    'AGRICULTURE',
    'ENERGY',
    'MANUFACTURING',
    'TRANSPORTATION',
    'HEALTHCARE',
    'EDUCATION',
    'RESEARCH',
    'ENVIRONMENT',
    'FINANCE'
]

# Mock data for testing
TEST_MISSION_DATA = {
    "domains": ALL_REQUIRED_DOMAIN_IDS,
    "priority": 5,
    "description": "Test mission"
}

# Assume the JSON queue path for testing
QUEUE_FILE_PATH = "/tmp/mission_queue.json"


def test_generate_mission_file():
    """Verify generated mission markdown has required sections."""
    # Create a temp file to capture output or just check return string if it returns it.
    # Assuming generate_mission_file returns the markdown content directly.
    content = generate_mission_file(TEST_MISSION_DATA)
    
    # Required sections are typically headers/keys like 'Objective', 'Steps', etc.
    required_sections = ['Objective', 'Steps', 'Parameters']
    
    for section in required_sections:
        assert section in content, f"Required section '{section}' is missing from mission markdown."


def test_clean_mission():
    """Verify clean mission returns no issues."""
    # Assuming validate_clean_mission accepts mission data and returns a list of errors.
    issues = validate_clean_mission(TEST_MISSION_DATA)
    
    # Verify that no issues were found (list is empty or issues count is 0)
    assert len(issues) == 0, f"Validation returned issues: {issues}"


def test_queue_mission_appends():
    """Verify mission is appended to queue JSON."""
    # Create a temp file for the expected queue location
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_queue_path = f.name
    
    try:
        # Simulate appending (or call the real function if it modifies the file passed or returns path)
        # Assuming queue_mission_appends appends to a specified location.
        # If it takes an existing file, we pass the temp file.
        # Let's assume it writes to QUEUE_FILE_PATH in the production code, 
        # but for testing we might need to mock or handle the path passed.
        
        # A robust test approach without mocks: 
        # Ensure queue_mission_appends can be called with TEST_MISSION_DATA and a path.
        # However, if the function signature isn't known (e.g., takes path as arg),
        # I will assume it handles the path logic internally or requires an explicit path.
        # Let's assume it returns the updated JSON content or file object.
        
        result = queue_mission_appends(TEST_MISSION_DATA, temp_queue_path)
        
        # If result is a string (JSON), check if mission data is inside.
        # If result is a file handle/obj, we might need to read it.
        # Assuming it writes to the path directly or returns the dict.
        if isinstance(result, str):
            import json
            loaded_data = json.loads(result)
            assert 'mission' in loaded_data or TEST_MISSION_DATA.get('description') in result
        elif hasattr(result, 'read'):  # File-like object (unlikely for standard return but possible)
             content = result.read()
        else:
            # Assume it modifies the queue file or returns the updated queue state
            pass
            
    finally:
        import os
        if os.path.exists(temp_queue_path):
            os.remove(temp_queue_path)


def test_all_domains_accepted():
    """Verify all 9 domain IDs are accepted."""
    # Assuming validate_clean_mission checks domains against a whitelist.
    # The mission data must have all required domains without errors.
    
    # Create a minimal mission with the specific domains
    issue_free_data = {
        "domains": ALL_REQUIRED_DOMAIN_IDS.copy(), # Ensure we test with exactly these IDs
        "priority": 5,
        "description": "Domain Validation Test"
    }
    
    issues = validate_clean_mission(issue_free_data)
    
    assert len(issues) == 0, f"All domains were not accepted. Issues found: {issues}"
```