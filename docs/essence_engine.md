# The Essence Engine: Intellectual Ingestion Architecture

This document defines the architecture of the **Data Gurgling** layer, the sensory organs of the Sovereign Financial Mega-Daemon.

## I. Source Registry
A central registry of all active intelligence sources.
- **Market Data**: OHLCV from primary exchanges.
- **Sentiment**: Social media pulses (Twitter, Reddit), news headlines.
- **Macro**: Economic calendars, treasury yields, CPI/PPI data.
- **Fundamental**: Earnings reports, balance sheets.

## II. The Inflow Protocol (`scripts/ingest_essence.py`)
A unified ingestion script that orchestrates the "gurgling" process.
1. **Poll**: Interrogate sources based on defined intervals.
2. **Acquire**: Securely pull the raw payload.
3. **Signature**: Cryptographically sign the raw data at the point of ingestion to prove no downstream tampering occurs.

## III. The Truth Ledger
A Fiduciary record stored in `intelligence/ledger.json`.
- **Entry**: `{source: "X", timestamp: "T", sha256: "H", signature: "S"}`
- **Persistence**: Raw payloads are stored in `intelligence/raw/` as binary blobs (Parquet/JSON).

## IV. The Essence Lab (`mantis_core/essence.py`)
The logic engine that extracts the "essence" from raw data.
- **Momentum Extraction**: Calculating velocity, acceleration, and flow from raw price and volume.
- **Truth Extraction**: Cross-referencing multiple sources to identify signal vs. noise.
- **Sentiment Distillation**: Converting raw headlines into a normalized `-1.0` to `+1.0` impulse.

## V. The Sovereign Influx
The interface for strategy integration.
- Strategies can query the `EssenceVault` for specific signals:
  ```python
  truth = self.context.intelligence.get_essence("BTC", "Sentiment")
  momentum = self.context.intelligence.get_essence("BTC", "Momentum")
  ```

## VI. Fiduciary Standards
- **Chain of Evidence**: Every trade decision must be linked to the specific Essence Ledger entry that justified it.
- **Non-Repudiation**: Data sources are verified; we do not ingest "phantom" data.
- **Determinism**: The extraction of essence must be deterministic for backtesting isomorphism.
