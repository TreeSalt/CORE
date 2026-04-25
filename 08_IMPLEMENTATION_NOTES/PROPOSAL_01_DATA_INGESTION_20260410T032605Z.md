---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import csv
from typing import List, Dict, Any, Iterator


class AbstractDataProvider:
    """Abstract base class for data providers."""
    
    def load_data(self) -> Any:
        """Load data from the source."""
        raise NotImplementedError
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all records as list of dictionaries."""
        raise NotImplementedError


class CsvDataProvider(AbstractDataProvider):
    """Implements AbstractDataProvider from a CSV file. Used for backtesting and replay."""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
    
    def _parse_csv(self) -> List[Dict[str, Any]]:
        """Parse CSV file into list of dictionaries."""
        records = []
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert values to appropriate types where possible
                    converted_row = {}
                    for key, value in row.items():
                        try:
                            # Try numeric conversion
                            if '.' in value:
                                converted_row[key] = float(value)
                            else:
                                converted_row[key] = int(value)
                        except ValueError:
                            converted_row[key] = value
                    records.append(converted_row)
            return records
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        except Exception as e:
            raise RuntimeError(f"Error parsing CSV file: {e}")
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load data from the CSV file."""
        return self._parse_csv()
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all records as list of dictionaries."""
        return self.load_data()
    
    def get_record_by_index(self, index: int) -> Dict[str, Any]:
        """Get a specific record by index."""
        records = self.get_records()
        if index < 0 or index >= len(records):
            raise IndexError(f"Index {index} out of range (0-{len(records)-1})")
        return records[index]
    
    def get_record_count(self) -> int:
        """Return the number of records."""
        records = self.get_records()
        return len(records)
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Enable iteration over records."""
        for record in self.get_records():
            yield record
    
    def get_column_values(self, column_name: str) -> List[Any]:
        """Get all values for a specific column."""
        return [record.get(column_name) for record in self.get_records()]
    
    def get_unique_column_values(self, column_name: str) -> set:
        """Get unique values for a column."""
        return set(self.get_column_values(column_name))
```