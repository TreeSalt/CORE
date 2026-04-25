---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Assuming ProposalExtractor class exists with an extract method
# from proposal_extractor import ProposalExtractor


class TestProposalExtractor:
    @pytest.fixture
    def extractor(self):
        return ProposalExtractor()

    def test_extract_works_with_valid_data(self, extractor):
        """Test that extraction works correctly with valid data."""
        # Setup mock file content
        sample_file = "proposal_name: John Doe\n"
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_file)
            temp_path = f.name
        
        try:
            # Call the extract method
            result = extractor.extract(temp_path)
            
            # Assert expected behavior
            assert result == ["John Doe"]  # Adjust based on actual return type
            
        finally:
            os.unlink(temp_path)
```