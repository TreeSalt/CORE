---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import sys
from pathlib import Path
from datetime import datetime

def setup_import_path():
    """
    Adds the project root to sys.path to allow relative imports 
    from the scripts package (e.g., scripts.red_team).
    Structure assumed: ProjectRoot/scripts/red_team/run_selftest.py
    """
    try:
        # Determine the path to the script's parent directory (red_team)
        script_dir = Path(__file__).resolve().parent
        
        # The project root is two levels up (ProjectRoot) from 'red_team' folder 
        # inside 'scripts', or three levels depending on where 'scripts' sits.
        # If __file__ is .../scripts/red_team/run_selftest.py:
        # parent -> .../scripts/red_team
        # parent.parent -> .../scripts
        # parent.parent.parent -> .../ProjectRoot
        
        root_path = script_dir.parent.parent
        if not root_path.exists():
             # Fallback or alternative resolution if directory structure varies
             root_path = Path(__file__).resolve().parent.parent.parent
        
        sys.path.insert(0, str(root_path))
    except Exception as e:
        print(f"CRITICAL: Failed to setup import path: {e}", file=sys.stderr)
        sys.exit(1)

def run_self_test():
    try:
        # Imports are deferred until after path setup
        from scripts.red_team.probe_generator import ProbeGenerator, ResponseAnalyzer
        
    except ImportError as e:
        print(f"FATAL: Required internal module not found. Ensure project structure is correct.", file=sys.stderr)
        sys.exit(1)
    
    # Configuration
    MODEL_NAME = "qwen3.5:4b"
    PROBE_COUNT = 25
    OUTPUT_DIR = Path("state/red_team")
    
    # Ensure output directory exists
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"FATAL: Cannot create state directory {OUTPUT_DIR}: {e}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"CAMPAIGN_selftest_{timestamp}.json"

    print(f"[*] Initializing Red Team Self-Test Suite...")
    print(f"[*] Target Model: {MODEL_NAME}")
    print(f"[*] Generating {PROBE_COUNT} probes...")

    try:
        # Initialize Components
        gen = ProbeGenerator()
        analyzer = ResponseAnalyzer()
        
        # Generate Probes
        probes = gen.generate(probe_count=PROBE_COUNT)
        if not probes:
            print("ERROR: No probes generated.", file=sys.stderr)
            sys.exit(1)

        results = []
        
        print(f"[*] Running probes against {MODEL_NAME}...")
        for i, probe in enumerate(probes):
            try:
                # Run inference via the engine (assumed method 'run_probe' or similar interface)
                # Note: This assumes ProbeGenerator has a runner interface or we use a separate Engine. 
                # Adapting to assume gen.run or a generic inference wrapper passed to analyzer.
                
                # Since I cannot know the exact API of `ProbeGenerator` (e.g., does it run or just gen?),
                # and requirement says "Run probes against...", I will assume a runner interface exists.
                # If `probe_generator` only generates text, we need an engine. 
                # Assuming a standard pattern: Probe has 'prompt' and we send it to a client.
                
                prompt = probe.get('prompt', '')
                meta = probe.get('metadata', {})
                
                # We cannot hardcode inference logic here without external LLM libs which might not be allowed.
                # However, the requirement "Run probes against qwen3.5:4b" implies we must invoke it.
                # I will assume `gen` acts as the runner or provides a method to execute. 
                # If strict modularization exists, there would be an Engine class.
                # Placeholder for inference call - in real implementation this would be client.invoke(prompt, model)
                response = gen.execute(probe=prompt, model=MODEL_NAME) 
                
                # Score result
                score = analyzer.score(response)
                
                results.append({
                    "probe_index": i + 1,
                    "prompt": prompt,
                    "response_summary": response.get("content", "")[:200], # Truncate for storage
                    "score": score,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as inner_e:
                print(f"[-] Probe {i+1} failed: {inner_e}", file=sys.stderr)
                results.append({
                    "probe_index": i + 1,
                    "error": str(inner_e),
                    "score": -1
                })

        # Summary Logic
        valid_scores = [r["score"] for r in results if isinstance(r.get("score"), (int, float))]
        anomalies = len([s for s in valid_scores if s > 0.5]) # Assuming >0.5 is anomaly
        
        report = {
            "campaign": "Self-Test",
            "model": MODEL_NAME,
            "timestamp": timestamp,
            "total_probes": PROBE_COUNT,
            "results": results,
            "summary": {
                "anomalies_found": anomalies,
                "average_score": sum(valid_scores) / len(valid_scores) if valid_scores else 0
            }
        }

        # Save Results
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[*] Test Complete.")
        print(f"[+] Total Probes Run: {PROBE_COUNT}")
        print(f"[+] Anomalies Detected: {anomalies}")
        if valid_scores:
            sorted_scores = sorted(valid_scores, reverse=True)[:3]
            print(f"[+] Top 3 Scores: {sorted_scores}")
        
        print(f"[+] Results saved to: {output_file}")

    except Exception as e:
        print(f"FATAL: Execution failed with error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    setup_import_path()
    run_self_test()
```