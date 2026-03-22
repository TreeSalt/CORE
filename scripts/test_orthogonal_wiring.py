from pathlib import Path

from mantis_core.config import StrategyParams
from mantis_core.data.sentiment_feed import SentimentFeed
from mantis_core.data_loader import ZeroCopyLoader
from mantis_core.portfolio_router import PortfolioRouter
from mantis_core.strategies.quarantine.EQ_SENTIMENT_v1.EQ_SENTIMENT_v1 import (
    EQSentimentV1,
)


def test_sentiment_wiring():
    # 1. Load Price Data (MES)
    price_path = Path("data/ibkr/mes_5m_ibkr_rth.parquet")
    if not price_path.exists():
        csv_path = Path("data/ibkr/mes_5m_ibkr_rth.csv")
        ZeroCopyLoader.convert_csv_to_parquet(csv_path)
    
    df_price = ZeroCopyLoader.load_market_data(price_path)
    print(f"Loaded {len(df_price)} price bars.")

    # 2. Load Sentiment Data (Lagged)
    sent_path = Path("tests/fixtures/synthetic/sentiment_feed.csv")
    feed = SentimentFeed.from_csv(sent_path, lag_seconds=300)
    print(f"Loaded sentiment feed with provenance: {feed.provenance_hash[:12]}")

    # 3. Align Sentiment (simulating harness logic)
    intelligence = feed.as_dict(df_price.index)
    
    # 4. Prepare Strategy
    strat = EQSentimentV1()
    params = StrategyParams(
        ma_length=200, 
        ma_fast=20, 
        rsi_length=14, 
        rsi_entry=30, 
        rsi_exit=70
    ) # valid params
    
    out = strat.prepare_data(df_price, params, intelligence=intelligence)
    
    print("\n--- Strategy Prepare Data Output ---")
    print(out[['sentiment_score', 'entry_signal', 'exit_signal']].dropna().head(10))
    
    # 5. Assertions
    # Bar at 08:35:00 should have 0.6 from 08:30:00 observation (300s lag)
    # Note: df_price has 5m bars.
    val_0835 = out.loc['2026-01-08 08:35:00-06:00']
    print(f"\nValue at 08:35:00-06:00: \n{val_0835[['sentiment_score', 'entry_signal']]}")
    
    assert val_0835['sentiment_score'] == 0.6
    assert val_0835['entry_signal']
    print("\n✅ Verification SUCCESS: Lag rule and signal logic confirmed.")

    # 6. Verify Destination Tagging in Router
    router = PortfolioRouter() # loads snapshot from default path
    router.capability_snapshot = {
        "primary_broker": "robinhood",
        "brokers": {
            "ibkr": {"supports": {"futures": True}},
            "robinhood": {"supports": {"crypto": True, "equities": True}}
        }
    }
    
    # Create fake weights to test routing
    fake_weights = {"MES": 1.0, "AAPL": 0.5, "BTC-USD": 0.2}
    
    # We need to simulate the resolve_broker part. 
    # Since route() normally calls _resolve_broker, let's just test our _resolve_broker logic
    print("\n--- Destination Resolution Test ---")
    for asset in fake_weights:
        broker = router._resolve_broker(asset)
        print(f"Asset: {asset:8} | Destination: {broker}")
    
    # Verify MES goes to IBKR (futures), BTC goes to robinhood (crypto), AAPL goes to robinhood (equities/default)
    # Note: snapshot says robinhood supports crypto=true, equities=true. ibkr supports futures=true.
    assert router._resolve_broker("MES") == "ibkr"
    assert router._resolve_broker("BTC-USD") == "robinhood"
    print("\n✅ Verification SUCCESS: Destination Broker Tagging confirmed.")

if __name__ == "__main__":
    test_sentiment_wiring()
