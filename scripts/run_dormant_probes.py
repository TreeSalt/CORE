#!/usr/bin/env python3
"""
scripts/run_dormant_probes.py — CORE-Native Jane Street Probe Runner
=====================================================================
Runs probes against Jane Street's Dormant LLM models locally.
No Colab required. Reads API key from .env.dormant (gitignored).

USAGE:
  .venv/bin/python3 scripts/run_dormant_probes.py
  .venv/bin/python3 scripts/run_dormant_probes.py --model dormant-model-1
  .venv/bin/python3 scripts/run_dormant_probes.py --round 2
"""
import asyncio
import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Ensure we can import jsinfer
try:
    from jsinfer import (
        BatchInferenceClient,
        Message,
        ActivationsRequest,
        ChatCompletionRequest,
    )
except ImportError:
    print("❌ jsinfer not installed. Run: .venv/bin/pip install jsinfer")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("❌ numpy not installed. Run: .venv/bin/pip install numpy")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE = REPO_ROOT / "state" / "dormant_puzzle"
ENV_FILE = REPO_ROOT / ".env.dormant"

MODELS = ["dormant-model-1", "dormant-model-2", "dormant-model-3"]
BATCH_SIZE = 5
SLEEP_BETWEEN = 3

# Bracketing: early / middle / late layers
ACTIVATION_LAYERS = [
    "model.layers.0.mlp.down_proj",
    "model.layers.15.mlp.down_proj",
    "model.layers.31.mlp.down_proj",
]


def load_api_key() -> str:
    """Load API key from .env.dormant (NEVER from source code)."""
    if not ENV_FILE.exists():
        print(f"❌ API key file not found: {ENV_FILE}")
        print(f"   Create it: echo 'DORMANT_API_KEY=your_key' > .env.dormant")
        sys.exit(1)
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("DORMANT_API_KEY="):
            return line.split("=", 1)[1].strip()
    print("❌ DORMANT_API_KEY not found in .env.dormant")
    sys.exit(1)


def load_probes(round_num: int) -> list:
    """Load probes for a specific round."""
    probe_file = STATE / f"PROBES_ROUND_{round_num}.json"
    if not probe_file.exists():
        print(f"❌ Probe file not found: {probe_file}")
        sys.exit(1)
    data = json.loads(probe_file.read_text())
    return data.get("probes", [])


def summarize_activations(result) -> dict:
    """Extract summary stats from raw activation data."""
    layer_stats = {}
    try:
        # Handle different response formats
        acts = None
        if hasattr(result, 'activations'):
            acts = result.activations
        elif isinstance(result, dict) and 'activations' in result:
            acts = result['activations']
        elif hasattr(result, '__dict__'):
            for attr in dir(result):
                if 'activ' in attr.lower():
                    acts = getattr(result, attr)
                    break

        if acts is None:
            return {"error": "no_activations_found", "raw_type": str(type(result))}

        if isinstance(acts, dict):
            items = acts.items()
        elif isinstance(acts, list):
            items = [(f"layer_{i}", v) for i, v in enumerate(acts)]
        else:
            return {"error": f"unexpected_type: {type(acts)}"}

        for layer_name, values in items:
            try:
                arr = np.array(values, dtype=float).flatten()
                layer_stats[str(layer_name)] = {
                    "mean": round(float(np.mean(arr)), 6),
                    "std": round(float(np.std(arr)), 6),
                    "max": round(float(np.max(arr)), 6),
                    "min": round(float(np.min(arr)), 6),
                    "l2_norm": round(float(np.linalg.norm(arr)), 6),
                    "num_elements": len(arr),
                    "top5_indices": [int(x) for x in np.argsort(np.abs(arr))[-5:]],
                    "top5_values": [round(float(arr[x]), 6) for x in np.argsort(np.abs(arr))[-5:]],
                }
            except Exception as e:
                layer_stats[str(layer_name)] = {"error": str(e)}

    except Exception as e:
        return {"error": str(e)}

    return layer_stats


async def run_probes(model: str, probes: list, client: BatchInferenceClient, round_num: int):
    """Run all probes against a single model, collecting chat + activations."""
    print(f"\n{'━'*60}")
    print(f"MODEL: {model} ({len(probes)} probes)")
    print(f"{'━'*60}")

    results = []

    for i in range(0, len(probes), BATCH_SIZE):
        batch = probes[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(probes) - 1) // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} probes)...")

        # ── CHAT COMPLETIONS ──
        chat_responses = {}
        try:
            chat_requests = [
                ChatCompletionRequest(
                    custom_id=p["id"],
                    messages=[Message(role="user", content=p["prompt"])],
                )
                for p in batch
            ]
            chat_results = await client.chat_completions(chat_requests, model=model)

            for probe, result in zip(batch, chat_results):
                resp = ""
                try:
                    if hasattr(result, 'choices') and result.choices:
                        resp = result.choices[0].message.content
                    elif isinstance(result, dict) and 'choices' in result:
                        resp = result['choices'][0]['message']['content']
                    else:
                        resp = str(result)[:500]
                except Exception:
                    resp = str(result)[:500]
                chat_responses[probe["id"]] = resp
        except Exception as e:
            print(f"    ⚠️  Chat error: {e}")
            for p in batch:
                chat_responses[p["id"]] = f"CHAT_ERROR: {e}"

        # ── ACTIVATIONS ──
        activation_data = {}
        try:
            act_requests = [
                ActivationsRequest(
                    custom_id=p["id"],
                    messages=[Message(role="user", content=p["prompt"])],
                    module_names=ACTIVATION_LAYERS,
                )
                for p in batch
            ]
            act_results = await client.activations(act_requests, model=model)

            for probe, result in zip(batch, act_results):
                activation_data[probe["id"]] = summarize_activations(result)
        except Exception as e:
            print(f"    ⚠️  Activation error: {e}")
            for p in batch:
                activation_data[p["id"]] = {"error": str(e)}

        # ── COMBINE ──
        for probe in batch:
            resp = chat_responses.get(probe["id"], "")
            results.append({
                "probe_id": probe["id"],
                "model": model,
                "category": probe["category"],
                "prompt": probe["prompt"],
                "response": resp,
                "response_length": len(resp.split()) if isinstance(resp, str) else 0,
                "activations": activation_data.get(probe["id"], {}),
                "anomaly_score": None,
                "notes": "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        print(f"    ✅ {len(batch)} probes complete")
        time.sleep(SLEEP_BETWEEN)

    # ── SAVE ──
    output_file = STATE / f"RESULTS_ROUND_{round_num}_{model.replace('-', '_')}.json"
    output_file.write_text(json.dumps({
        "model": model,
        "round": round_num,
        "probe_count": len(results),
        "activation_layers": ACTIVATION_LAYERS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }, indent=2))

    print(f"  📋 Saved: {output_file.name} ({len(results)} results)")
    return results


async def main():
    parser = argparse.ArgumentParser(description="CORE Dormant Puzzle Probe Runner")
    parser.add_argument("--model", default=None, help="Specific model (default: all 3)")
    parser.add_argument("--round", type=int, default=1, help="Probe round number")
    args = parser.parse_args()

    print("=" * 60)
    print("CORE — JANE STREET DORMANT PUZZLE PROBE RUNNER")
    print("=" * 60)

    # Load API key securely
    api_key = load_api_key()
    print(f"🔑 API key loaded from .env.dormant")

    # Load probes
    probes = load_probes(args.round)
    print(f"📋 Loaded {len(probes)} probes (Round {args.round})")

    # Initialize client
    client = BatchInferenceClient()
    client.set_api_key(api_key)
    print(f"🔗 Client connected")

    # Determine which models to test
    models = [args.model] if args.model else MODELS

    # Run
    all_results = []
    for model in models:
        results = await run_probes(model, probes, client, args.round)
        all_results.extend(results)

    # Summary
    print(f"\n{'='*60}")
    print(f"PROBE RUN COMPLETE")
    print(f"{'='*60}")
    print(f"Total probes executed: {len(all_results)}")
    print(f"Models tested: {', '.join(models)}")
    print(f"\nNext: .venv/bin/python3 scripts/analyze_dormant_results.py")


if __name__ == "__main__":
    asyncio.run(main())
