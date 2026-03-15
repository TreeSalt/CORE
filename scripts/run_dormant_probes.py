#!/usr/bin/env python3
"""
scripts/run_dormant_probes.py — CORE-Native Dormant Puzzle Probe Runner v3
===========================================================================
Patches applied from Gemini's strategic review:
  - Exponential backoff on rate limit / timeout errors
  - Cosine similarity baseline tracking in activation summaries
  - Retry logic that preserves API quota

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

try:
    from jsinfer import (
        BatchInferenceClient, Message, ActivationsRequest, ChatCompletionRequest,
    )
except ImportError:
    print("Run: .venv/bin/pip install jsinfer")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Run: .venv/bin/pip install numpy")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE = REPO_ROOT / "state" / "dormant_puzzle"
ENV_FILE = REPO_ROOT / ".env.dormant"

MODELS = ["dormant-model-1", "dormant-model-2", "dormant-model-3"]
BATCH_SIZE = 5
SLEEP_BETWEEN = 3
MAX_RETRIES = 4
INITIAL_BACKOFF = 30  # seconds

ACTIVATION_LAYERS = [
    "model.layers.0.mlp.down_proj",
    "model.layers.15.mlp.down_proj",
    "model.layers.31.mlp.down_proj",
]


def load_api_key():
    if not ENV_FILE.exists():
        print(f"Create: echo 'DORMANT_API_KEY=your_key' > .env.dormant")
        sys.exit(1)
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("DORMANT_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit(1)


def load_probes(round_num):
    probe_file = STATE / f"PROBES_ROUND_{round_num}.json"
    if not probe_file.exists():
        print(f"Not found: {probe_file}")
        sys.exit(1)
    return json.loads(probe_file.read_text()).get("probes", [])


def summarize_activations(result):
    """Extract stats + raw flattened vectors for cosine similarity later."""
    layer_stats = {}
    try:
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

        items = acts.items() if isinstance(acts, dict) else [(f"layer_{i}", v) for i, v in enumerate(acts)]

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
                    # Store compact vector for cosine similarity
                    # (first 256 dims — enough for directional comparison)
                    "vector_sample": [round(float(x), 4) for x in arr[:256]],
                }
            except Exception as e:
                layer_stats[str(layer_name)] = {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
    return layer_stats


async def api_call_with_backoff(coro_func, description="API call"):
    """Execute an async API call with exponential backoff on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_func()
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(x in err_str for x in ["429", "rate", "limit", "quota", "timeout", "cancelled"])

            if is_rate_limit and attempt < MAX_RETRIES - 1:
                wait = INITIAL_BACKOFF * (2 ** attempt)
                print(f"    ⏳ {description} rate limited. Waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
                await asyncio.sleep(wait)
            elif attempt < MAX_RETRIES - 1:
                wait = 5 * (attempt + 1)
                print(f"    ⚠️  {description} error: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                print(f"    ❌ {description} failed after {MAX_RETRIES} attempts: {e}")
                raise
    raise RuntimeError(f"{description} exhausted all retries")


async def run_probes(model, probes, client, round_num):
    print(f"\n{'━'*60}")
    print(f"MODEL: {model} ({len(probes)} probes)")
    print(f"{'━'*60}")

    results = []

    for i in range(0, len(probes), BATCH_SIZE):
        batch = probes[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(probes) - 1) // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} probes)...")

        # ── CHAT COMPLETIONS (with backoff) ──
        chat_responses = {}
        try:
            chat_requests = [
                ChatCompletionRequest(
                    custom_id=p["id"],
                    messages=[Message(role="user", content=p["prompt"])],
                ) for p in batch
            ]

            chat_results = await api_call_with_backoff(
                lambda: client.chat_completions(chat_requests, model=model),
                f"Chat batch {batch_num}"
            )

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
            print(f"    ❌ Chat batch failed permanently: {e}")
            for p in batch:
                chat_responses[p["id"]] = f"CHAT_ERROR: {e}"

        # ── ACTIVATIONS (with backoff) ──
        activation_data = {}
        try:
            act_requests = [
                ActivationsRequest(
                    custom_id=p["id"],
                    messages=[Message(role="user", content=p["prompt"])],
                    module_names=ACTIVATION_LAYERS,
                ) for p in batch
            ]

            act_results = await api_call_with_backoff(
                lambda: client.activations(act_requests, model=model),
                f"Activation batch {batch_num}"
            )

            for probe, result in zip(batch, act_results):
                activation_data[probe["id"]] = summarize_activations(result)
        except Exception as e:
            print(f"    ❌ Activation batch failed permanently: {e}")
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
        await asyncio.sleep(SLEEP_BETWEEN)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--round", type=int, default=1)
    args = parser.parse_args()

    print("=" * 60)
    print("CORE — DORMANT PUZZLE PROBE RUNNER v3")
    print("  Exponential backoff: ON")
    print("  Activation vectors: ON (256-dim sample)")
    print("  Layers: 0 / 15 / 31 (bracketing)")
    print("=" * 60)

    api_key = load_api_key()
    print(f"🔑 API key loaded")

    probes = load_probes(args.round)
    print(f"📋 {len(probes)} probes (Round {args.round})")

    client = BatchInferenceClient()
    client.set_api_key(api_key)

    models = [args.model] if args.model else MODELS

    all_results = []
    for model in models:
        results = await run_probes(model, probes, client, args.round)
        all_results.extend(results)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(all_results)} probes across {len(models)} models")
    print(f"Next: .venv/bin/python3 scripts/analyze_dormant_results.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
