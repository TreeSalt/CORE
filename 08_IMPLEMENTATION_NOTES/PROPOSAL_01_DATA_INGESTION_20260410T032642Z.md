---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pandas as pd


class AbstractDataProvider:
    def __init__(self):
        pass
    
    def load(self):
        raise NotImplementedError
    
    def get_data(self):
        raise NotImplementedError


class CsvDataProvider(AbstractDataProvider):
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.data = None
        
    def load(self):
        if self.data is None:
            self.data = pd.read_csv(self.csv_path)
            
    def get_data(self):
        self.load()
        return self.data
```