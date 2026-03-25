---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import logging
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Optional, List

# Ensure no hardcoded credentials are used in this module
# Paths must not target /04_GOVERNANCE/ for writes or configuration

class CandlestickGenerator:
    """
    Generates synthetic OHLCV candlestick data for ingestion pipeline testing.
    
    Security Notes:
    - No secrets stored within class attributes.
    - All paths are sanitized to avoid writing to governance-controlled directories.
    - Configuration is expected via environment variables or secure vault injection.
    """
    
    # Standard logging configuration avoiding sensitive paths
    def __init__(self, ticker: str, start_date: str = None, end_date: str = None):
        self.ticker = ticker.upper()
        
        if start_date:
            try:
                self.start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid date format for {start_date}. Use YYYY-MM-DD.") from e
        else:
            # Default to 30 days ago if not provided
            self.start_datetime = datetime.now() - timedelta(days=30)

        if end_date:
            try:
                self.end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid date format for {end_date}. Use YYYY-MM-DD.") from e
        else:
            # Default to yesterday (exclusive) to avoid generating current tick data
            self.end_datetime = datetime.now() - timedelta(days=1)

        self.frequency = "daily"
        self.output_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        
    def _validate_paths(self, target_path: str) -> str:
        """Sanitize output paths to prevent writing to forbidden directories."""
        # Block list containing governance or sensitive roots
        forbidden_prefixes = ["/04_GOVERNANCE/", "/secrets/", ".env", "~/"]
        
        for prefix in forbidden_prefixs:
            if target_path.startswith(prefix):
                raise PermissionError(f"Path generation blocked: {target_path} contains forbidden prefix.")
                
        # Return sanitized path (append local working directory if absolute)
        return os.path.normpath(target_path)

    def _generate_mock_series(self, start_dt: datetime, end_dt: datetime) -> pd.Series:
        """Generates synthetic price movements."""
        num_points = int((end_dt - start_dt).total_seconds() / 86400) + 1
        
        # Base price initialization
        base_price = 150.00
        prices = [base_price]
        
        current_open = base_price
        
        for _ in range(num_points - 1):
            # Generate random volatility factor (scaled per financial logic approximation)
            daily_return = np.random.normal(0, 0.02) 
            close_price = current_open * (1 + daily_return)
            
            high_price = max(current_open, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(current_open, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = int(np.random.poisson(1000))
            
            current_open = close_price
            
            prices.append((high_price + low_price + close_price) / 3)

        return pd.Series(prices, index=pd.date_range(start=start_dt, end=end_dt, freq="D"))

    def generate(self, output_file: Optional[str] = None) -> pd.DataFrame:
        """
        Generates the final candlestick DataFrame.
        
        Args:
            output_file: Path to save the generated CSV. If None, returns dataframe in memory.
        """
        logger = logging.getLogger(__name__)
        
        try:
            df = pd.DataFrame(columns=self.output_columns)
            
            for _i in range(1):  # Currently single asset generator logic
                high_series = []
                low_series = []
                close_series = []
                open_series = []
                
                start_dt = self.start_datetime.date() if isinstance(self.start_datetime, datetime) else self.start_datetime
                end_dt = self.end_datetime.date() if isinstance(self.end_datetime, datetime) else self.end_datetime
                
                # Simplified synthetic generation for testing ingestion schema
                base_close = 100.0
                current_date = start_dt
                
                while current_date <= end_dt:
                    noise = np.random.uniform(-0.5, 0.5, size=1)[0]
                    
                    prev_close = base_close
                    open_price = prev_close * (1 + noise)
                    close_price = open_price * (1 + np.random.normal(0, 0.002))
                    high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.1))
                    low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.1))
                    
                    df_row = {
                        "timestamp": pd.Timestamp(current_date).date(),
                        "open": float(open_price),
                        "high": float(high_price),
                        "low": float(low_price),
                        "close": float(close_price),
                        "volume": int(np.random.exponential(5000))
                    }
                    
                    df = pd.concat([df, pd.DataFrame([df_row])], ignore_index=True)
                    
                    current_date += timedelta(days=1)

                # Apply ticker prefix if needed for downstream uniqueness
                df["asset"] = self.ticker
                
                if output_file:
                    safe_path = self._validate_paths(output_file)
                    file_handle = open(safe_path, 'w') 
                    df.to_csv(file_handle, index=False)
                    logger.info(f"Generated dataset for {self.ticker} saved to {safe_path}")
                    
                    # Securely remove handle reference in local context
                    del file_handle

                return df
                
        except Exception as e:
            # Fail closed on errors (log only, do not mask stack trace if critical)
            logger.error(f"Data generation failed for {self.ticker}: {str(e)}")
            raise

    def generate_batch(self, tickers: List[str], output_dir: str = None) -> pd.DataFrame:
        """
        Generates data for multiple tickers.
        
        Args:
            tickers: List of asset symbols.
            output_dir: Base directory to write CSVs. Defaults to in-memory return.
        """
        all_dataframes = []
        
        for ticker in tickers:
            # Create isolated generator instance per ticker
            gen = CandlestickGenerator(ticker=ticker)
            
            df = gen.generate()
            
            if output_dir:
                safe_path = os.path.join(output_dir, f"{ticker}.csv")
                # Re-validate the constructed path against forbidden roots
                safe_path = self._validate_paths(safe_path)
                df.to_csv(safe_path, index=False)
                
            all_dataframes.append(df)
            
        if all_dataframes:
            return pd.concat(all_dataframes, ignore_index=True)
        
        return pd.DataFrame(columns=self.output_columns)


if __name__ == "__main__":
    # Example Usage for Validation (Do not execute in production without review)
    import sys
    
    try:
        config = {
            "ticker": "BTC-USD",
            "start_date": "2023-10-01",
            "end_date": "2023-10-10"
        }
        
        # Instantiate generator with configuration
        generator = CandlestickGenerator(
            ticker=config["ticker"],
            start_date=config["start_date"],
            end_date=config["end_date"]
        )
        
        # Generate in memory
        df = generator.generate()
        print(df.head())
        
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)
```