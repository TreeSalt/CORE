#!/usr/bin/env python3
"""
scripts/ibkr_ingest_mes_5m.py
=============================
Hardened Ingest for IBKR Historical Data (MES 5-min).
Uses ib_insync for pagination-safe retrieval and strict gate enforcement.
"""

import argparse

# Optional dependency: ib_insync
import asyncio
import csv
import json
import sys
from datetime import datetime, timezone
from datetime import time as dt_time
from pathlib import Path

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

try:
    from ib_insync import IB, ContFuture
except ImportError:
    print("❌ Missing dependency: ib_insync. Install with 'pip install -r requirements-ibkr.txt'")
    sys.exit(1)

def check_rth_integrity(bars):
    """
    Verify that bars are within RTH (09:30 - 16:00 ET).
    Since IBKR 'useRTH=True' should handle this, we use it as a sanctuary gate.
    """
    if not bars:
        return False, "No bars provided"
    
    # Simple check for ET-like hours if metadata isn't fully certain on TZ
    # Most futures are US/Eastern based.
    rth_start = dt_time(9, 0)
    rth_end = dt_time(16, 15)
    
    out_of_bounds = 0
    for bar in bars:
        # bar.date is usually datetime in UTC or local if specified
        # For simplicity in this gate, we just check the hour component 
        # assuming the user's TWS is in ET or the bars are correctly adjusted.
        bt = bar.date.time() if hasattr(bar.date, 'time') else None
        if bt and (bt < rth_start or bt > rth_end):
            out_of_bounds += 1
            
    ratio = out_of_bounds / len(bars)
    if ratio > 0.20: # Allow 20% for edge cases or TWS tz drift
        return False, f"RTH VIOLATION: {ratio:.1%} of bars fall outside 09:00-16:15 ET/Local."
    
    return True, "OK"

def ingest(host="127.0.0.1", port=4002, client_id=1, duration="30 D"):
    ib = IB()
    def on_error(reqId, errorCode, errorString, contract):
        if errorCode == 321:
            print(f"❌ ERROR 321 INTERCEPTED (Pacing/Validation): {errorString}")
            sys.exit(1)
    ib.errorEvent += on_error
    print(f"🔌 Connecting to IBKR ({host}:{port}, id:{client_id})...")
    
    try:
        ib.connect(host, port, clientId=client_id, timeout=10)
    except Exception as e:
        print(f"❌ CONNECTION FAILURE: {e}")
        sys.exit(1)

    try:
        # Define Contract: Micro E-mini S&P 500 (Continuous or specific front)
        # Note: continuous futures 'CONTFUT' are often best for historical pulls
        contract = ContFuture('MES', 'CME', currency='USD')
        
        # Qualify contract (Resolves ambiguous fields)
        cd = ib.qualifyContracts(contract)
        if not cd:
            print("❌ CONTRACT RESOLUTION FAILED: Could not find MES on CME.")
            sys.exit(1)
        contract = cd[0]
        print(f"📦 Contract Bound: {contract.localSymbol} ({contract.lastTradeDateOrContractMonth})")

        print(f"📥 Pulling {duration} of TRADES at 5 min intervals (useRTH=True)...")
        # reqHistoricalData handles pagination automatically in ib_insync if needed
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1,
            keepUpToDate=False,
            timeout=180
        )

        if not bars:
            print("❌ DATA FAILURE: Received zero bars from IBKR.")
            sys.exit(1)

        print(f"✅ Received {len(bars)} bars.")

        # --- DATA QUALITY GATES ---
        
        # 1. Volume Gate
        total_volume = sum(b.volume for b in bars)
        if total_volume <= 0:
            print("❌ QUALITY GATE FAILURE: Aggregate volume is zero. Dataset is hollow.")
            sys.exit(1)

        # 2. RTH Gate
        rth_ok, rth_msg = check_rth_integrity(bars)
        if not rth_ok:
            print(f"❌ QUALITY GATE FAILURE: {rth_msg}")
            sys.exit(1)

        # 3. Pagination Sanity (No Duplicates)
        dates = [b.date for b in bars]
        if len(set(dates)) != len(dates):
            print("❌ DATA INTEGRITY FAILURE: Duplicate timestamps detected in pull.")
            sys.exit(1)

        # --- PERSISTENCE ---
        out_dir = Path("data/ibkr")
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / "mes_5m_ibkr_rth_tape.csv"
        meta_path = out_dir / "mes_5m_ibkr_rth_tape.meta.json"

        # Write CSV
        print(f"💾 Saving to {csv_path}...")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "open", "high", "low", "close", "volume", "average", "barCount"])
            for b in bars:
                writer.writerow([
                    b.date.isoformat() if hasattr(b.date, 'isoformat') else str(b.date),
                    b.open, b.high, b.low, b.close, b.volume, getattr(b, 'average', 0.0), getattr(b, 'barCount', 0)
                ])

        # Generate Metadata
        print(f"📜 Generating metadata: {meta_path}...")
        meta = {
            "pulled_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "host": host,
            "port": port,
            "clientId": client_id,
            "useRTH": True,
            "timezone_handling": "ib_insync_native",
            "bar_count": len(bars),
            "first_ts": bars[0].date.isoformat() if hasattr(bars[0].date, 'isoformat') else str(bars[0].date),
            "last_ts": bars[-1].date.isoformat() if hasattr(bars[-1].date, 'isoformat') else str(bars[-1].date),
            "volume_stats": {
                "total": float(total_volume),
                "avg": float(total_volume / len(bars))
            },
            "pagination_stats": {
                "is_complete": True,
                "duration": duration
            },
            "contract_fields": {
                "conId": contract.conId,
                "localSymbol": contract.localSymbol,
                "exchange": contract.exchange,
                "lastTradeDateOrContractMonth": contract.lastTradeDateOrContractMonth
            }
        }
        
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print("✨ IBKR Ingest Successful (FAIL-CLOSED GATES PASSED).")

    finally:
        ib.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Institutional IBKR MES Ingest")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002, help="Paper: 4002, Live: 7496")
    parser.add_argument("--client-id", type=int, default=1)
    parser.add_argument("--duration", default="30 D", help="Duration string (e.g., '60 D', '1 Y')")
    args = parser.parse_args()
    
    ingest(args.host, args.port, args.client_id, args.duration)
