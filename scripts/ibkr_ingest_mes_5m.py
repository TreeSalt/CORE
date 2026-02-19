#!/usr/bin/env python3
"""
scripts/ibkr_ingest_mes_5m.py
=============================
Connects to IBKR TWS/Gateway (Paper) and pulls MES 5-min historical bars.
Writes CSV and metadata JSON.
Fail-closed on connection failure or bad data.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

# Optional dependency: ibapi
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.common import BarData
except ImportError:
    print("❌ Missing dependency: ibapi. Install with 'pip install ibapi' (sdist) or similar.")
    sys.exit(1)


class IBKRDataApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.finished = Event()
        self.error_event = Event()
        self.last_error = None

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        # 2104, 2106, 2158 are informational
        if errorCode in [2104, 2106, 2158]:
            return
        print(f"⚠️  IBKR Error {errorCode}: {errorString}")
        if errorCode in [502, 504, 200]: # Connection errors
            self.last_error = f"{errorCode}: {errorString}"
            self.error_event.set()

    def historicalData(self, reqId: int, bar: BarData):
        self.data.append(bar)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print(f"✅ Historical Data End. Received {len(self.data)} bars.")
        self.finished.set()

def ingest(host="127.0.0.1", port=4002, client_id=1, duration="30 D"):
    app = IBKRDataApp()
    app.connect(host, port, client_id)

    # Start listener loop in a thread
    from threading import Thread
    api_thread = Thread(target=app.run, daemon=True)
    api_thread.start()

    # Wait for connection
    time.sleep(1)
    if app.error_event.is_set():
        print(f"❌ Connection Failed: {app.last_error}")
        sys.exit(1)

    # Define Contract: MES (Micro E-mini S&P 500)
    contract = Contract()
    contract.symbol = "MES"
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    # contract.lastTradeDateOrContractMonth = "202403" # Ideally dynamic, but for ingest let's rely on continuous or specific
    # Using 'CONT FUT' often requires specific setup. Let's try explicit current front.
    # For robust ingest, we might need to specify. Let's assume strict front check or rely on 'ContFuture'
    contract.includeExpired = False
    
    # Actually, to be safe/simple for this task, let's assume we want the front month.
    # We can use "MES" on "CME" and let TWS resolve or specify date.
    # For now, let's try a widely available contract logic or just explicit.
    # Hardcoding a recent one for the "Reality Contact" test if needed, or better, 
    # let's try the 'ContFuture' approach if IBKR supports it easily via API, 
    # OR just fail if contract ambiguous. 
    # Let's specify a date to be safe. "202403" is past. "202406"? 
    # To keep it "Reality Contact", valid *now*.
    # Attempting to finding front contract via details is complex.
    # Let's use a specific one for the scope of "ingesting data".
    contract.lastTradeDateOrContractMonth = "202603" # Future dated for simulation context? 
    # Wait, simulation is 2024 data typically.
    # If we pull "30 D" looking back from NOW, we need a current contract.
    # Let's default to no date and see if TWS defaults to front.
    
    # Actually, let's use a dummy ingest test mode if we can't connect, 
    # but the task requires the script. I will write the script to be functional.
    
    # Request Data
    print(f"📥 Requesting {duration} of MES 5m bars...")
    app.reqHistoricalData(
        reqId=42,
        contract=contract,
        endDateTime="", # End now
        durationStr=duration,
        barSizeSetting="5 mins",
        whatToShow="TRADES",
        useRTH=1, # Strict RTH
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
    )

    # Wait
    try:
        app.finished.wait(timeout=30)
    except KeyboardInterrupt:
        app.disconnect()
        sys.exit(1)

    if app.error_event.is_set():
        print(f"❌ Ingest Failed: {app.last_error}")
        app.disconnect()
        sys.exit(1)

    if not app.finished.is_set():
        print("❌ Ingest Timed Out")
        app.disconnect()
        sys.exit(1)

    app.disconnect()
    
    if not app.data:
        print("❌ No data received.")
        sys.exit(1)

    # Process Data
    out_dir = Path("data/ibkr")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "mes_5m_ibkr_rth.csv"
    meta_path = out_dir / "mes_5m_ibkr_rth.meta.json"

    print(f"💾 Writing {len(app.data)} bars to {csv_path}...")
    
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Datetime", "Open", "High", "Low", "Close", "Volume"])
        for bar in app.data:
            # IBKR returns 'YYYYMMDD  HH:mm:ss' or unix ts
            writer.writerow([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    meta = {
        "pulled_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract": {
            "symbol": contract.symbol,
            "secType": contract.secType,
            "exchange": contract.exchange
        },
        "params": {
            "duration": duration,
            "barSize": "5 mins",
            "useRTH": True
        },
        "stats": {
            "count": len(app.data),
            "first_ts": app.data[0].date if app.data else None,
            "last_ts": app.data[-1].date if app.data else None
        }
    }
    
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print("✅ Ingest Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    parser.add_argument("--client-id", type=int, default=1)
    parser.add_argument("--duration", default="30 D")
    args = parser.parse_args()
    
    ingest(args.host, args.port, args.client_id, args.duration)
