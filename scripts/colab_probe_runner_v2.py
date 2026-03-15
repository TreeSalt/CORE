###############################################################################
# COLAB PROBE RUNNER v2 — Copy this ENTIRE cell into Google Colab
# Captures BOTH chat completions AND activation vectors
# Run AFTER setup cells (Step 0-2) are complete
###############################################################################

import json
import time
from datetime import datetime, timezone

# ── CONFIG ──────────────────────────────────────────────────────────────────
MODELS = ["dormant-model-1", "dormant-model-2", "dormant-model-3"]
ROUND_FILE = "PROBES_ROUND_1.json"  # Upload this from state/dormant_puzzle/
BATCH_SIZE = 5  # Probes per API call (keep small to avoid timeouts)
SLEEP_BETWEEN = 3  # Seconds between batches (rate limit courtesy)

# Activation layers to probe (bracketing strategy):
#   Layer 0 = input processing
#   Layer 15 = middle representation  
#   Layer 31 = near-output (adjust if model has different depth)
ACTIVATION_LAYERS = [
    "model.layers.0.mlp.down_proj",
    "model.layers.15.mlp.down_proj",
    "model.layers.31.mlp.down_proj",
]

# ── LOAD PROBES ─────────────────────────────────────────────────────────────
with open(ROUND_FILE) as f:
    probes = json.load(f)["probes"]
print(f"Loaded {len(probes)} probes")

# ── EXECUTE PER MODEL ───────────────────────────────────────────────────────
for MODEL in MODELS:
    print(f"\n{'='*60}")
    print(f"MODEL: {MODEL}")
    print(f"{'='*60}")
    
    results = []
    
    for i in range(0, len(probes), BATCH_SIZE):
        batch = probes[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(probes) - 1) // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} probes)...")
        
        # ── CHAT COMPLETIONS ──
        chat_requests = [
            ChatCompletionRequest(
                custom_id=probe["id"],
                messages=[Message(role="user", content=probe["prompt"])],
            )
            for probe in batch
        ]
        
        chat_responses = {}
        try:
            chat_results = await client.chat_completions(chat_requests, model=MODEL)
            for probe, result in zip(batch, chat_results):
                resp = ""
                if hasattr(result, 'choices') and result.choices:
                    resp = result.choices[0].message.content
                elif isinstance(result, dict) and 'choices' in result:
                    resp = result['choices'][0]['message']['content']
                else:
                    resp = str(result)
                chat_responses[probe["id"]] = resp
        except Exception as e:
            print(f"    Chat error: {e}")
            for probe in batch:
                chat_responses[probe["id"]] = f"CHAT_ERROR: {e}"
        
        # ── ACTIVATIONS ──
        activation_requests = [
            ActivationsRequest(
                custom_id=probe["id"],
                messages=[Message(role="user", content=probe["prompt"])],
                module_names=ACTIVATION_LAYERS,
            )
            for probe in batch
        ]
        
        activation_data = {}
        try:
            act_results = await client.activations(activation_requests, model=MODEL)
            for probe, result in zip(batch, act_results):
                # Extract activation summary stats (not full vectors — too large)
                layer_stats = {}
                try:
                    if hasattr(result, 'activations'):
                        acts = result.activations
                    elif isinstance(result, dict) and 'activations' in result:
                        acts = result['activations']
                    else:
                        acts = {}
                    
                    for layer_name, values in acts.items():
                        import numpy as np
                        arr = np.array(values) if not isinstance(values, np.ndarray) else values
                        # Flatten if multi-dimensional
                        arr = arr.flatten()
                        layer_stats[layer_name] = {
                            "mean": float(np.mean(arr)),
                            "std": float(np.std(arr)),
                            "max": float(np.max(arr)),
                            "min": float(np.min(arr)),
                            "l2_norm": float(np.linalg.norm(arr)),
                            "num_elements": len(arr),
                            # Top 5 activation indices (where signal is strongest)
                            "top5_indices": [int(x) for x in np.argsort(np.abs(arr))[-5:]],
                            "top5_values": [float(arr[x]) for x in np.argsort(np.abs(arr))[-5:]],
                        }
                except Exception as ae:
                    layer_stats = {"error": str(ae)}
                
                activation_data[probe["id"]] = layer_stats
        except Exception as e:
            print(f"    Activation error: {e}")
            for probe in batch:
                activation_data[probe["id"]] = {"error": str(e)}
        
        # ── COMBINE ──
        for probe in batch:
            response_text = chat_responses.get(probe["id"], "")
            results.append({
                "probe_id": probe["id"],
                "model": MODEL,
                "category": probe["category"],
                "prompt": probe["prompt"],
                "response": response_text,
                "response_length": len(response_text.split()) if isinstance(response_text, str) else 0,
                "activations": activation_data.get(probe["id"], {}),
                "anomaly_score": None,  # Human fills in later
                "notes": "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        
        time.sleep(SLEEP_BETWEEN)
    
    # ── SAVE PER MODEL ──
    output_file = f"RESULTS_ROUND_1_{MODEL.replace('-', '_')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": MODEL,
            "round": 1,
            "probe_count": len(results),
            "activation_layers": ACTIVATION_LAYERS,
            "results": results,
        }, f, indent=2)
    
    print(f"  ✅ Saved: {output_file} ({len(results)} results)")

print(f"\n{'='*60}")
print("ALL MODELS COMPLETE")
print(f"Download these files from the Colab sidebar:")
for m in MODELS:
    print(f"  RESULTS_ROUND_1_{m.replace('-', '_')}.json")
print(f"Then copy to ~/TRADER_OPS/v9e_stage/state/dormant_puzzle/")
print(f"{'='*60}")
