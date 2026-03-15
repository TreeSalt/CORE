#!/usr/bin/env python3
"""
COLAB HELPER — Copy this into your Google Colab notebook
=========================================================
This runs all probes from a round file against a specific model
and saves the results. Copy-paste into Colab after setup.

USAGE (in Colab):
  1. Upload your PROBES_ROUND_N.json file to Colab
  2. Run this code
  3. Download the RESULTS_ROUND_N_MODEL_X.json file
  4. Copy it to ~/TRADER_OPS/v9e_stage/state/dormant_puzzle/
"""
import json
import time
from datetime import datetime, timezone

# ── CONFIG ──
MODEL = "dormant-model-1"  # Change to 2 or 3 for each model
ROUND_FILE = "PROBES_ROUND_1.json"
OUTPUT_FILE = f"RESULTS_ROUND_1_{MODEL.replace('-', '_')}.json"

# ── LOAD PROBES ──
with open(ROUND_FILE) as f:
    probes = json.load(f)["probes"]

print(f"Loaded {len(probes)} probes for {MODEL}")

# ── EXECUTE ──
results = []
batch_size = 5  # Adjust based on rate limits

for i in range(0, len(probes), batch_size):
    batch = probes[i:i+batch_size]
    print(f"Batch {i//batch_size + 1}/{(len(probes)-1)//batch_size + 1}...")
    
    # Build chat completion requests
    requests = [
        ChatCompletionRequest(
            custom_id=probe["id"],
            messages=[Message(role="user", content=probe["prompt"])],
        )
        for probe in batch
    ]
    
    # Execute
    try:
        chat_results = await client.chat_completions(requests, model=MODEL)
        
        for probe, result in zip(batch, chat_results):
            response_text = result.choices[0].message.content if result.choices else ""
            results.append({
                "probe_id": probe["id"],
                "model": MODEL,
                "category": probe["category"],
                "prompt": probe["prompt"],
                "response": response_text,
                "response_length": len(response_text.split()),
                "anomaly_score": None,  # Human fills in later
                "notes": "",
                "activations_collected": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as e:
        print(f"  Error: {e}")
        for probe in batch:
            results.append({
                "probe_id": probe["id"],
                "model": MODEL,
                "category": probe["category"],
                "prompt": probe["prompt"],
                "response": f"ERROR: {e}",
                "response_length": 0,
                "anomaly_score": None,
                "notes": "API error",
                "activations_collected": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    
    time.sleep(2)  # Rate limit courtesy

# ── SAVE ──
with open(OUTPUT_FILE, "w") as f:
    json.dump({"model": MODEL, "round": 1, "results": results}, f, indent=2)

print(f"\nDone! {len(results)} results saved to {OUTPUT_FILE}")
print(f"Download this file and copy to ~/TRADER_OPS/v9e_stage/state/dormant_puzzle/")
