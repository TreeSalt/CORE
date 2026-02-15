# antigravity_harness/data_loader.py
from pathlib import Path

import pandas as pd

try:
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


class ZeroCopyLoader:
    @staticmethod
    def load_market_data(path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path}")
        if path.suffix != ".parquet":
            raise ValueError("THE DRAGON FORBIDS CSV.")

        if not HAS_PYARROW:
            raise ImportError("pyarrow is required for Parquet support.")

        table = pq.read_table(path, memory_map=True)
        df = table.to_pandas(self_destruct=True, split_blocks=True)
        return df

    @staticmethod
    def convert_csv_to_parquet(csv_path: Path):
        df = pd.read_csv(csv_path)
        parquet_path = csv_path.with_suffix(".parquet")
        df.to_parquet(parquet_path, compression="snappy", index=False)
        print(f"⚡ [SPEED] Transmuted {csv_path.name} to Binary Artifact.")
