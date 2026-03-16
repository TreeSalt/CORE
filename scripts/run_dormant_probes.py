#!/usr/bin/env python3
"""
scripts/run_dormant_probes.py — CORE-Native Dormant Puzzle Probe Runner v6
===========================================================================
FIXED: jsinfer returns custom_id strings, not response objects.
Actual responses live in /tmp/*/aggregate_results.json files.

Council review history:
  v1: Chat-only (Claude). Gemini caught missing activations.
  v2: Added activation collection. Gemini caught async sleep blocking.
  v3: Exponential backoff. Gemini caught first-256 slicing fallacy.
  v4: Strided sampling, MAD outlier rejection, hard clutch.
  v5: Fixed response parsing — FIXED: dict .get(custom_id) access.
"""
import asyncio
import json
import sys
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
INITIAL_BACKOFF = 30

ACTIVATION_LAYERS = [
    "model.layers.0.mlp.down_proj",
    "model.layers.15.mlp.down_proj",
    "model.layers.31.mlp.down_proj",
]


def load_api_key():
    if not ENV_FILE.exists():
        sys.exit("Create: echo 'DORMANT_API_KEY=your_key' > .env.dormant")
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("DORMANT_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("DORMANT_API_KEY not found in .env.dormant")


def load_probes(round_num):
    probe_file = STATE / f"PROBES_ROUND_{round_num}.json"
    if not probe_file.exists():
        sys.exit(f"Not found: {probe_file}")
    return json.loads(probe_file.read_text()).get("probes", [])


def find_newest_aggregate(after_ts):
    """Find aggregate_results.json files created after a timestamp."""
    candidates = glob.glob("/tmp/tmp*/batch_*/aggregate_results.json")
    new_files = [f for f in candidates if os.path.getmtime(f) > after_ts]
    if new_files:
        return max(new_files, key=os.path.getmtime)
    if candidates:
        return max(candidates, key=os.path.getmtime)
    return None


def read_aggregate(agg_path):
    """Parse aggregate_results.json → dict keyed by custom_id."""
    if not agg_path or not os.path.exists(agg_path):
        return {}
    try:
        data = json.loads(Path(agg_path).read_text())
        results = {}
        for cid, entry in data.items():
            results[cid] = entry
        return results
    except Exception as e:
        print(f"    ⚠️  Aggregate parse error: {e}")
        return {}


def extract_chat_response(entry):
    """Extract assistant text from a response object or dict."""
    if isinstance(entry, str):
        return entry
    # Object with .choices (standard OpenAI format)
    if hasattr(entry, "choices") and entry.choices:
        return entry.choices[0].message.content
    # Dict with messages (aggregate format)
    if isinstance(entry, dict):
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        if "choices" in entry:
            return entry["choices"][0]["message"]["content"]
    # Object with .messages
    if hasattr(entry, "messages"):
        for msg in entry.messages:
            if hasattr(msg, "role") and msg.role == "assistant":
                return msg.content if hasattr(msg, "content") else str(msg)
    return str(entry)[:500]


def extract_activation_stats(entry):
    """Extract numeric activation data from an aggregate entry."""
    layer_stats = {}
    if not isinstance(entry, dict):
        return {"error": f"unexpected_type: {type(entry)}"}

    for key, values in entry.items():
        if key in ("custom_id", "messages", "role", "content"):
            continue
        try:
            arr = np.array(values, dtype=float).flatten()
            if len(arr) < 10:
                continue
            stride = max(1, len(arr) // 256)
            layer_stats[str(key)] = {
                "mean": round(float(np.mean(arr)), 6),
                "std": round(float(np.std(arr)), 6),
                "max": round(float(np.max(arr)), 6),
                "min": round(float(np.min(arr)), 6),
                "l2_norm": round(float(np.linalg.norm(arr)), 6),
                "num_elements": len(arr),
                "vector_sample": [round(float(x), 4) for x in arr[::stride]],
            }
        except (ValueError, TypeError):
            continue

    return layer_stats if layer_stats else {"error": "no_numeric_data"}


async def api_call_with_backoff(coro_func, description="API call"):
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_func()
        except Exception as e:
            err_str = str(e).lower()
            is_rate = any(x in err_str for x in ["429", "rate", "limit", "quota", "timeout", "cancelled"])
            if attempt < MAX_RETRIES - 1:
                wait = INITIAL_BACKOFF * (2 ** attempt) if is_rate else 5 * (attempt + 1)
                print(f"    ⏳ {description}: {e}. Retry in {wait}s ({attempt+1}/{MAX_RETRIES})")
                await asyncio.sleep(wait)
            else:
                raise


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

        # ── CHAT COMPLETIONS ──
        chat_responses = {}
        try:
            chat_results = await api_call_with_backoff(
                lambda: client.chat_completions(
                    [ChatCompletionRequest(custom_id=p["id"],
                     messages=[Message(role="user", content=p["prompt"])])
                     for p in batch],
                    model=model,
                ),
                f"Chat batch {batch_num}"
            )
            for p in batch:
                obj = chat_results.get(p["id"]) if isinstance(chat_results, dict) else None
                if obj is not None:
                    resp = extract_chat_response(obj)
                else:
                    resp = f"KEY_MISSING:{p['id']}"
                chat_responses[p["id"]] = resp
                preview = resp[:70].replace('\n', ' ') if isinstance(resp, str) else str(resp)[:70]
                print(f"    [{p['id']}] {preview}")
        except Exception as e:
            print(f"    ❌ Chat failed: {e}")
            for p in batch:
                chat_responses[p["id"]] = f"CHAT_ERROR: {e}"

        # ── ACTIVATIONS ──
        activation_data = {}
        try:
            act_results = await api_call_with_backoff(
                lambda: client.activations(
                    [ActivationsRequest(custom_id=p["id"],
                     messages=[Message(role="user", content=p["prompt"])],
                     module_names=ACTIVATION_LAYERS)
                     for p in batch],
                    model=model,
                ),
                f"Activation batch {batch_num}"
            )
            for p in batch:
                obj = act_results.get(p["id"]) if isinstance(act_results, dict) else None
                if obj is not None and hasattr(obj, "activations"):
                    # obj.activations is a dict of {layer_name: numpy.ndarray}
                    layer_stats = {}
                    for layer_name, arr in obj.activations.items():
                        import numpy as np
                        arr = np.array(arr).flatten()
                        stride = max(1, len(arr) // 256)
                        layer_stats[layer_name] = {
                            "mean": round(float(np.mean(arr)), 6),
                            "std": round(float(np.std(arr)), 6),
                            "max": round(float(np.max(arr)), 6),
                            "min": round(float(np.min(arr)), 6),
                            "l2_norm": round(float(np.linalg.norm(arr)), 6),
                            "num_elements": len(arr),
                            "vector_sample": [round(float(x), 4) for x in arr[::stride]],
                        }
                    activation_data[p["id"]] = layer_stats
                    print(f"    [{p['id']}] 🔬 {len(layer_stats)} layers captured")
                else:
                    activation_data[p["id"]] = {"error": "no_activation_obj"}
        except Exception as e:
            print(f"    ❌ Activations failed: {e}")
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

        # ── HARD CLUTCH ──
        err_count = sum(1 for r in results[-len(batch):]
                        if "ERROR" in str(r.get("response", ""))
                        and "error" in str(r.get("activations", {})))
        if err_count == len(batch):
            print(f"\n    🛑 HARD CLUTCH: saving {len(results)} partial results")
            partial = STATE / f"RESULTS_ROUND_{round_num}_{model.replace('-','_')}_PARTIAL.json"
            partial.write_text(json.dumps({
                "model": model, "round": round_num, "status": "PARTIAL",
                "completed": len(results), "total": len(probes),
                "resume_from": i + BATCH_SIZE,
                "results": results,
            }, indent=2))
            return results

        print(f"    ✅ Batch {batch_num} done")
        await asyncio.sleep(SLEEP_BETWEEN)

    # ── SAVE ──
    out = STATE / f"RESULTS_ROUND_{round_num}_{model.replace('-','_')}.json"
    out.write_text(json.dumps({
        "model": model, "round": round_num, "probe_count": len(results),
        "activation_layers": ACTIVATION_LAYERS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }, indent=2))
    print(f"  📋 Saved: {out.name} ({len(results)} results)")
    return results


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--round", type=int, default=1)
    args = parser.parse_args()

    print("=" * 60)
    print("CORE — DORMANT PUZZLE PROBE RUNNER v5")
    print("=" * 60)

    client = BatchInferenceClient()
    client.set_api_key(load_api_key())
    print(f"🔑 API key loaded")

    probes = load_probes(args.round)
    print(f"📋 {len(probes)} probes (Round {args.round})")

    models = [args.model] if args.model else MODELS
    for model in models:
        await run_probes(model, probes, client, args.round)

    print(f"\n{'='*60}")
    print("Next: .venv/bin/python3 scripts/analyze_dormant_results.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
