---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import pandas as pd
from pathlib import Path

class CsvDataProvider:
    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        self._data = None
        
    def _load(self):
        if self._data is None:
            try:
                self._data = pd.read_csv(self.csv_path)
            except FileNotFoundError:
                raise
            
    def get_data(self, start_date=None, end_date=None):
        self._load()
        df = self._data.copy()
        # Filter based on 'date' column if available and dates provided
        if 'date' in df.columns and (start_date is not None or end_date is not None):
            df['date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date) if start_date else None
            end = pd.to_datetime(end_date) if end_date else None
            
            # Construct filter conditions safely
            conditions = []
            if start:
                conditions.append(df['date'] >= start)
            if end:
                conditions.append(df['date'] <= end)
                
            if conditions:
                df = df[conditions]
                
        return df