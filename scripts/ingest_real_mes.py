import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fix import order for ruff
from antigravity_harness.data import DataConfig, load_ohlc

# REPO_ROOT used for path construction
REPO_ROOT = Path(__file__).parent.parent


def main():
    print("🦅 Sovereign Ingestion: Contacting Real World...")
    
    symbol = "MES=F"
    interval = "5m"
    
    # Range: Last 4 weeks
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(weeks=4)
    
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    print(f"  [i] Target: {symbol} ({interval})")
    print(f"  [i] Window: {start_str} to {end_str}")
    
    cfg = DataConfig(interval=interval)
    
    try:
        # load_ohlc handles yfinance, split adjustments, and caching
        df = load_ohlc(symbol, start_str, end_str, cfg)
        
        if df.empty:
            print("⛔ FATAL: No data returned.")
            sys.exit(1)
            
        print(f"✅ Received {len(df)} bars.")
        
        # Replace synthetic file with real data
        target_path = REPO_ROOT / "tests" / "fixtures" / "synthetic" / "mes_5m_synthetic.csv"
        print(f"💾 Overwriting {target_path.name} with REAL data...")
        
        # Ensure we keep index (timestamps)
        df.to_csv(target_path)
        
        print("✨ Ingestion successful. Filename preserved for pipeline compatibility.")
        
    except Exception as e:
        print(f"⛔ FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
