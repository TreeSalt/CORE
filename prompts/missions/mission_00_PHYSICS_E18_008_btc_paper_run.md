# MISSION: mantis_btc_paper_run
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_008_btc_paper_run

## DELIVERABLE
File: scripts/mantis_btc_paper_run.py

## SCOPE
Standalone script that runs the v2 pipeline against BTC/USD via Alpaca
paper trading for 1 hour and captures the results. Reads ALPACA_API_KEY
and ALPACA_SECRET_KEY from env. Writes results to reports/btc_paper_run_<timestamp>.json.
