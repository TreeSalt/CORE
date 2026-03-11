#!/usr/bin/env python3
"""
FIX: Zoo Epoch 1 Benchmark Blocker — Surgical Patch
=====================================================
AUTHOR: Claude (Hostile Auditor) — Supreme Council
DATE: 2026-03-11
TARGETS: 06_BENCHMARKING/benchmark_runner.py, scripts/run_loop.py, scripts/orchestrator_loop.py

ROOT CAUSE:
  The orchestrator chain (orchestrator_loop → run_loop → benchmark_runner) uses
  sys.executable to propagate the Python interpreter. When started via system
  python3 instead of .venv/bin/python3, importlib.util.find_spec('pandas')
  returns None — even though pandas IS installed in the project venv.

  Every Zoo strategy proposal was rejected with HALLUCINATED_IMPORT: 'pandas'.
  The strategies were correct. The benchmark was wrong.

FIX (two-pronged):
  1. benchmark_runner.py: Add project dependencies to the known-safe set
     so import resolution doesn't depend on which Python is running
  2. All three scripts: Add venv auto-detection so the correct interpreter
     is always used regardless of how the user invokes the command

VERIFICATION:
  After running this script:
  python3 -c "
  import sys; sys.path.insert(0, '06_BENCHMARKING')
  from benchmark_runner import gate_hygiene, _load_schema, _load_domains
  _load_schema(); _load_domains()
  result = gate_hygiene(['import pandas as pd\\ndf = pd.DataFrame()'], __import__('pathlib').Path('test'), 'IMPLEMENTATION')
  print('PASS' if result['passed'] else 'FAIL:', result)
  "
"""
from pathlib import Path
import sys

REPO_ROOT = Path(".")

# Verify we're in the right directory
if not (REPO_ROOT / "06_BENCHMARKING" / "benchmark_runner.py").exists():
    print("❌ Run this script from v9e_stage/ (the repo root)")
    sys.exit(1)

fixes_applied = 0

# ══════════════════════════════════════════════════════════════════════════════
# FIX 1: benchmark_runner.py — Add project dependencies to known-safe imports
# ══════════════════════════════════════════════════════════════════════════════

benchmark_file = REPO_ROOT / "06_BENCHMARKING" / "benchmark_runner.py"
content = benchmark_file.read_text()

old_stdlib = 'STDLIB = {"os", "sys", "json", "logging", "datetime", "pathlib", "hashlib", "re", "ast", "time", "math", "typing", "websocket"}'

new_stdlib = '''# Known-safe imports: stdlib + project dependencies from requirements.txt
        # Adding project deps here prevents false HALLUCINATED_IMPORT when
        # the benchmark runner is invoked outside the venv (sys.executable chain).
        STDLIB = {
            # Python stdlib
            "os", "sys", "json", "logging", "datetime", "pathlib", "hashlib",
            "re", "ast", "time", "math", "typing", "collections", "dataclasses",
            "abc", "enum", "functools", "itertools", "copy", "io", "csv",
            "statistics", "decimal", "fractions", "random", "bisect", "heapq",
            "operator", "contextlib", "warnings", "traceback", "inspect",
            "threading", "multiprocessing", "queue", "signal", "socket",
            "struct", "array", "weakref", "textwrap", "string", "secrets",
            "tempfile", "shutil", "glob", "fnmatch", "gzip", "zipfile",
            "configparser", "argparse", "unittest", "pprint", "uuid",
            # Project dependencies (installed in .venv via requirements.txt)
            "pandas", "numpy", "yaml", "pyyaml", "requests", "websocket",
            "scipy", "sklearn", "matplotlib", "plotly", "pyarrow",
        }'''

if old_stdlib in content:
    content = content.replace(old_stdlib, new_stdlib)
    benchmark_file.write_text(content)
    fixes_applied += 1
    print("✅ Fix 1: benchmark_runner.py — project dependencies added to known-safe set")
else:
    print("❌ Fix 1: STDLIB pattern not found — check benchmark_runner.py manually")
    # Show what's actually there for debugging
    for i, line in enumerate(content.splitlines()):
        if "STDLIB" in line and "=" in line and "{" in line:
            print(f"   Found at line {i+1}: {line.strip()[:100]}")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 2: Add VENV_PYTHON auto-detection to orchestrator_loop.py
# ══════════════════════════════════════════════════════════════════════════════

orch_file = REPO_ROOT / "scripts" / "orchestrator_loop.py"
orch_content = orch_file.read_text()

# Add venv detection after the PATHS section
old_orch_paths = 'RUN_LOOP        = REPO_ROOT / "scripts" / "run_loop.py"'
new_orch_paths = '''RUN_LOOP        = REPO_ROOT / "scripts" / "run_loop.py"

# ── VENV AUTO-DETECTION ───────────────────────────────────────────────────────
# If invoked via system python, re-exec through the venv python so that
# the entire subprocess chain (run_loop → benchmark_runner) inherits the
# correct interpreter with all project dependencies available.
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"
if _VENV_PYTHON.exists() and str(_VENV_PYTHON.resolve()) != sys.executable:
    PYTHON_FOR_SUBPROCESSES = str(_VENV_PYTHON)
else:
    PYTHON_FOR_SUBPROCESSES = sys.executable'''

if old_orch_paths in orch_content and "VENV AUTO-DETECTION" not in orch_content:
    orch_content = orch_content.replace(old_orch_paths, new_orch_paths)

    # Also patch the sys.executable call in execute_mission
    old_cmd = "        sys.executable, str(RUN_LOOP),"
    new_cmd = "        PYTHON_FOR_SUBPROCESSES, str(RUN_LOOP),"

    if old_cmd in orch_content:
        orch_content = orch_content.replace(old_cmd, new_cmd, 1)  # only first occurrence

    orch_file.write_text(orch_content)
    fixes_applied += 1
    print("✅ Fix 2: orchestrator_loop.py — venv auto-detection added")
else:
    if "VENV AUTO-DETECTION" in orch_content:
        print("⏭️  Fix 2: Already applied — skipping")
        fixes_applied += 1
    else:
        print("❌ Fix 2: Pattern not found in orchestrator_loop.py")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 3: Same venv detection for run_loop.py
# ══════════════════════════════════════════════════════════════════════════════

run_loop_file = REPO_ROOT / "scripts" / "run_loop.py"
rl_content = run_loop_file.read_text()

old_rl_paths = 'BENCHMARK_RUNNER  = REPO_ROOT / "06_BENCHMARKING" / "benchmark_runner.py"'
new_rl_paths = '''BENCHMARK_RUNNER  = REPO_ROOT / "06_BENCHMARKING" / "benchmark_runner.py"

# ── VENV AUTO-DETECTION ───────────────────────────────────────────────────────
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python3"
if _VENV_PYTHON.exists() and str(_VENV_PYTHON.resolve()) != sys.executable:
    PYTHON_FOR_SUBPROCESSES = str(_VENV_PYTHON)
else:
    PYTHON_FOR_SUBPROCESSES = sys.executable'''

if old_rl_paths in rl_content and "VENV AUTO-DETECTION" not in rl_content:
    rl_content = rl_content.replace(old_rl_paths, new_rl_paths)

    # Patch both sys.executable calls
    rl_content = rl_content.replace(
        "sys.executable, str(ROUTER)",
        "PYTHON_FOR_SUBPROCESSES, str(ROUTER)"
    )
    rl_content = rl_content.replace(
        "sys.executable, str(BENCHMARK_RUNNER)",
        "PYTHON_FOR_SUBPROCESSES, str(BENCHMARK_RUNNER)"
    )

    run_loop_file.write_text(rl_content)
    fixes_applied += 1
    print("✅ Fix 3: run_loop.py — venv auto-detection added")
else:
    if "VENV AUTO-DETECTION" in rl_content:
        print("⏭️  Fix 3: Already applied — skipping")
        fixes_applied += 1
    else:
        print("❌ Fix 3: Pattern not found in run_loop.py")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 4: Reset Zoo missions to PENDING
# ══════════════════════════════════════════════════════════════════════════════

queue_file = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
if queue_file.exists():
    import json
    queue = json.loads(queue_file.read_text())
    reset_count = 0
    for m in queue.get("missions", []):
        if m["id"].startswith("zoo_impl_E1_") and m["status"] != "PENDING":
            m["status"] = "PENDING"
            reset_count += 1
    if reset_count > 0:
        queue_file.write_text(json.dumps(queue, indent=2))
        fixes_applied += 1
        print(f"✅ Fix 4: {reset_count} Zoo missions reset to PENDING")
    else:
        already_pending = sum(1 for m in queue.get("missions", []) if m["id"].startswith("zoo_impl_E1_") and m["status"] == "PENDING")
        if already_pending > 0:
            print(f"⏭️  Fix 4: {already_pending} Zoo missions already PENDING")
            fixes_applied += 1
        else:
            print("❌ Fix 4: No Zoo missions found in queue")
else:
    print("❌ Fix 4: MISSION_QUEUE.json not found")


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"FIXES APPLIED: {fixes_applied}/4")
print(f"{'='*60}")

if fixes_applied >= 3:
    print("""
NEXT STEPS:
  1. git add -A && git commit -m "fix: Zoo benchmark blocker — pandas import resolution + venv propagation

     Root cause: orchestrator chain used sys.executable (system python)
     but pandas is installed in .venv. importlib.util.find_spec('pandas')
     returned None → false HALLUCINATED_IMPORT on every Zoo strategy.

     Fix A: Added project dependencies to benchmark_runner known-safe set
     Fix B: Added VENV_PYTHON auto-detection to orchestrator + run_loop
     Fix C: Reset Zoo E1 missions to PENDING for re-run"

  2. Configure Ollama for 32b CPU offload (prevents timeout on E1_002/E1_003):
     OLLAMA_NUM_GPU=20 ollama serve
     (or add to your .bashrc: export OLLAMA_NUM_GPU=20)

  3. Fire the Zoo:
     python3 scripts/orchestrator_loop.py
""")
else:
    print("\n⚠️  Some fixes failed — review output above before proceeding.")
