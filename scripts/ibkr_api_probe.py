#!/usr/bin/env python3
"""
scripts/ibkr_api_probe.py
=========================
Fail-closed API probe for IBKR Gateway.
Validates that not only the port is open, but the API is responsive and ready.
"""
import argparse
import asyncio
import sys

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

try:
    from ib_insync import IB
except ImportError:
    print("❌ Missing dependency: ib_insync. Cannot probe API.")
    sys.exit(1)

def probe(host="127.0.0.1", port=4002, client_id=999):
    ib = IB()
    try:
        # Short timeout for fail-fast behavior
        ib.connect(host, port, clientId=client_id, timeout=3.0)
        t = ib.reqCurrentTime()
        if t:
            print(f"✅ API Responsive: Target {host}:{port} is fully ready. (Exchange Time: {t})")
            sys.exit(0)
        else:
            print(f"❌ API Unresponsive: Connected to {host}:{port} but reqCurrentTime failed.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ API Probe failed for {host}:{port}: {e}")
        sys.exit(1)
    finally:
        ib.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Probe IBKR API readiness.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    parser.add_argument("--client-id", type=int, default=999)
    args = parser.parse_args()
    probe(args.host, args.port, args.client_id)
