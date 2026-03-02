import sys
import threading
import time
import os

def watchdog():
    time.sleep(30)
    print("Watchdog timeout!")
    sys.stdout.flush()
    os._exit(1)

t = threading.Thread(target=watchdog)
t.daemon = True
t.start()

print("Trace starting...")
sys.stdout.flush()

try:
    print("Trace importing pandas...")
    sys.stdout.flush()
    import pandas as pd
    
    print("Trace importing antigravity_harness.portfolio_policies...")
    sys.stdout.flush()
    from antigravity_harness.portfolio_policies import CrossSectionMeanReversionPolicy

    print("Trace importing antigravity_harness.regimes...")
    sys.stdout.flush()
    from antigravity_harness.regimes import RegimeConfig

    print("Trace everything imported successfully!")
    sys.stdout.flush()
except Exception as e:
    print("Trace error:", e)
    sys.stdout.flush()
print("Trace end")
