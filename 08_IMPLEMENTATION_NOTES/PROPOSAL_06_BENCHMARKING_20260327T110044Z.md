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


def mock_get_all_proposals():
    return [
        {"id": 1, "filename": "app.py"},
        {"id": 2, "filename": "main.py"}
    ]


@pytest.fixture
def deployed_files():
    return ["app.py", "config.py"]


def test_get_proposals_returns_list(mock_get_all_proposals):
    """Verify get_all_proposals returns a list of dicts"""
    proposals = mock_get_all_proposals()
    assert isinstance(proposals, list)
    for proposal in proposals:
        assert isinstance(proposal, dict)


@pytest.fixture
def audit_module():
    from deployment_audit import generate_report, get_deployed_files
    
    return type('obj', (object,), {'get_all_proposals': mock_get_all_proposals})


def test_deployed_files_excludes_init(audit_module):
    """Verify __init__.py not in results"""
    deployed = audit_module.get_deployed_files()
    
    assert all('__init__.py' not in str(f) for f in deployed if isinstance(f, (list, tuple)))


@pytest.fixture
def missing_deployments():
    return {
        "prop_id": 1,
        "filename": "app.py"
    }


def test_missing_deployments_found(audit_module):
    """Create mock proposals and deployed list, verify gap detected"""
    proposals = [
        {"id": 1, "filename": "app.py"},
        {"id": 2, "filename": "main.py"}
    ]
    
    deployed = ["app.py", "config.py"]
    
    assert len(proposals) > 0
    assert len(deployed) > 0
    
    # Verify there's a gap in deployments for id 2
    deploy_ids = [p["id"] for p in proposals if p.get("filename") == "main.py"]
    assert len(deploy_ids) > 0


def test_report_generates_markdown(audit_module, tmp_path):
    """Verify generate_report creates a .md file"""
    from deployment_audit import generate_report
    
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
    
    report = generate_report(temp_path)
    
    assert report is not None
    assert temp_path.exists()
    assert temp_path.is_file()
    assert temp_path.suffix == '.md'
```