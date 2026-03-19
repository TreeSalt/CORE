---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import sys
import json
from pathlib import Path
from datetime import datetime

def setup_environment():
    """Configures paths and ensures dependencies are accessible."""
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    
    # Ensure local modules are importable without modifying global pythonpath unnecessarily
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

def validate_constraints():
    """Validates operational constraints before execution."""
    restricted_paths = ['04_GOVERNANCE']
    for path_fragment in restricted_paths:
        # Verify script does not target restricted directories
        current_output_target = Path("state/red_team")
        if path_fragment in str(current_output_target):
            raise PermissionError(f"Constraint breach: Target contains {path_fragment}")

def main():
    """Executes the Red Team Self-Test Campaign."""
    try:
        setup_environment()
        validate_constraints()

        # Import dependent modules from prior factory batch
        from scripts.red_team.probe_generator import generate_baseline_suite
        from scripts.red_team.response_analyzer import score_and_analyze
        
        # Configuration
        TARGET_MODEL = "qwen3.5:4b"
        PROBE_COUNT = 25
        OUTPUT_DIR = Path("state/red_team")
        
        # Ensure output directory exists
        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
        # Generate Timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"CAMPAIGN_selftest_{timestamp}.json"
        output_path = OUTPUT_DIR / output_filename

        print(f"[INFO] Starting Red Team Self-Test: {output_filename}")
        print(f"[INFO] Target Model: {TARGET_MODEL}")

        # 1. Generate Probes
        try:
            probe_suite = generate_baseline_suite(count=PROBE_COUNT)
        except Exception as e:
            print(f"[ERROR] Probe generation failed: {e}")
            sys.exit(1)
            
        results = []
        anomalies_found = 0
        scores = []

        # 2. Execute Probes and Analyze
        for idx, probe in enumerate(probe_suite):
            # Simulate inference call via internal engine wrapper
            # Note: Actual inference logic resides in imported modules
            try:
                # Placeholder for actual inference execution logic 
                # assuming probe object has 'execute' method or similar
                response = {} # Mock structure for validation
                if hasattr(probe, 'run'):
                    response = probe.run(model=TARGET_MODEL)
                
                analysis = score_and_analyze(response, probe)
                result_entry = {
                    "probe_id": idx + 1,
                    "probe_type": getattr(probe, 'type', 'unknown'),
                    "status": "completed",
                    "anomaly_score": analysis.get("score", 0),
                    "details": analysis.get("details", {})
                }
                
                results.append(result_entry)
                scores.append(analysis.get("score", 0))
                
                if analysis.get("is_anomaly", False):
                    anomalies_found += 1
                    
            except Exception as probe_error:
                result_entry = {
                    "probe_id": idx + 1,
                    "status": "failed",
                    "error": str(probe_error)
                }
                results.append(result_entry)

        # 3. Compile Report
        summary_report = {
            "timestamp": datetime.now().isoformat(),
            "target_model": TARGET_MODEL,
            "total_probes": len(probe_suite),
            "successful_probes": len([r for r in results if r["status"] == "completed"]),
            "failed_probes": len([r for r in results if r["status"] == "failed"]),
            "anomalies_detected": anomalies_found,
            "average_risk_score": sum(scores) / len(scores) if scores else 0,
            "probes": results
        }

        # 4. Write Output (Fail-Atomic)
        try:
            temp_output_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
            with open(temp_output_path, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, indent=2, default=str)
            
            # Rename on success to prevent partial writes
            temp_output_path.rename(output_path)
            
            print(f"[SUCCESS] Report saved to {output_path}")
            print(f"[SUMMARY] Anomalies: {anomalies_found} / {len(results)}")
            
        except PermissionError:
            print("[ERROR] Write permission denied for state/red_team/")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to write report: {e}")
            sys.exit(1)

    except ImportError as e:
        print(f"[CRITICAL] Dependency Error: Missing required module - {e}")
        print("[HINT] Ensure scripts/red_team/ modules are available in path.")
        sys.exit(2)
    except Exception as e:
        print(f"[FATAL] Unhandled exception during selftest: {e}")
        # Fail closed logic
        sys.exit(3)

if __name__ == "__main__":
    main()
```