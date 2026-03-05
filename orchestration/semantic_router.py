#!/usr/bin/env python3
"""
semantic_router.py — Fiduciary ZeroClaw Semantic Router

Central nervous system for routing orchestration tasks to the appropriate
local LLM profile based on task complexity tags.

Profiles:
    Sprinter     — Qwen 7B / DeepSeek 8B (GPU, fast)   → LOW complexity
    Heavy Lifter — Qwen 32B (CPU-offloaded, thorough)   → HIGH complexity

Hardware Target:
    GPU:  GTX 1070 8GB VRAM
    RAM:  40GB System RAM
"""

import re
import sys
import json
import logging
import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _find_repo_root() -> Path:
    """
    Dynamically resolve the TRADER_OPS repository root by walking upward
    from this script's location until we find the .git directory or the
    STATE_SYNC.md sentinel file.  This makes the router CWD-independent —
    it works whether invoked from the repo root, v9e_stage/, or anywhere else.
    """
    candidate = Path(__file__).resolve().parent
    while candidate != candidate.parent:  # stop at filesystem root
        if (candidate / ".git").is_dir() or (candidate / "STATE_SYNC.md").is_file():
            return candidate
        candidate = candidate.parent
    # Fallback: assume the immediate parent of orchestration/ is the root
    return Path(__file__).resolve().parent.parent


REPO_ROOT = _find_repo_root()
STATE_SYNC_PATH = REPO_ROOT / "STATE_SYNC.md"
TASK_COMPLEXITY_PATH = REPO_ROOT / "TASK_COMPLEXITY.md"
MISSION_CONTROL_DIR = REPO_ROOT / "00_MISSION_CONTROL"

OLLAMA_BASE_URL = "http://localhost:11434"

# ---------------------------------------------------------------------------
# Profile Definitions
# ---------------------------------------------------------------------------

@dataclass
class LLMProfile:
    """Defines a local LLM routing profile."""
    name: str
    model: str
    description: str
    max_tokens: int = 2048
    temperature: float = 0.3
    gpu_layers: int = -1          # -1 = all layers on GPU
    context_window: int = 8192
    tags: list = field(default_factory=list)


PROFILES = {
    "sprinter": LLMProfile(
        name="Sprinter",
        model="qwen2.5:7b",
        description="Fast inference for low-complexity tasks (unit tests, syntax, formatting)",
        max_tokens=2048,
        temperature=0.2,
        gpu_layers=-1,             # fully GPU-resident on GTX 1070
        context_window=8192,
        tags=["unit_test", "syntax", "formatting", "lint", "docstring", "commit_msg"],
    ),
    "heavy_lifter": LLMProfile(
        name="Heavy Lifter",
        model="qwen2.5:32b",
        description="Deep reasoning for high-complexity tasks (fiduciary math, architecture)",
        max_tokens=4096,
        temperature=0.1,
        gpu_layers=0,              # fully CPU-offloaded to system RAM
        context_window=16384,
        tags=["fiduciary", "architecture", "risk", "quantitative", "physics", "refactor"],
    ),
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("SemanticRouter")

# ---------------------------------------------------------------------------
# Task Parser
# ---------------------------------------------------------------------------

# Matches: COMPLEXITY: LOW  or  COMPLEXITY: HIGH  (case-insensitive)
COMPLEXITY_RE = re.compile(
    r"COMPLEXITY:\s*(LOW|HIGH)",
    re.IGNORECASE,
)

# Matches: TASK: "..." or TASK: '...'
TASK_RE = re.compile(
    r'TASK:\s*["\'](.+?)["\']',
    re.IGNORECASE,
)

# HTML comment tags in STATE_SYNC: <!-- COMPLEXITY: LOW -->
COMMENT_COMPLEXITY_RE = re.compile(
    r"<!--\s*COMPLEXITY:\s*(LOW|HIGH)\s*-->",
    re.IGNORECASE,
)


@dataclass
class RoutedTask:
    """A parsed task with its complexity classification and routed profile."""
    description: str
    complexity: str              # "LOW" or "HIGH"
    profile: LLMProfile
    source_file: str


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ```) so examples aren't parsed as tasks."""
    return re.sub(r"```[\s\S]*?```", "", text)


def parse_complexity_from_file(filepath: Path) -> list[RoutedTask]:
    """
    Parse COMPLEXITY tags from a markdown file.
    Supports both YAML-style blocks and HTML comment annotations.
    Code blocks are stripped first so documentation examples are ignored.
    """
    if not filepath.exists():
        log.warning(f"File not found: {filepath}")
        return []

    raw_text = filepath.read_text(encoding="utf-8")
    tasks: list[RoutedTask] = []

    # Strip fenced code blocks to avoid matching documentation examples
    text = _strip_code_blocks(raw_text)

    # --- Parse YAML-style blocks (skip matches inside HTML comments) ---
    blocks = COMPLEXITY_RE.finditer(text)
    for match in blocks:
        # Skip if this match is inside an HTML comment (handled below)
        surrounding = text[max(0, match.start() - 10):match.end() + 10]
        if "<!--" in surrounding and "-->" in surrounding:
            continue

        complexity = match.group(1).upper()
        # Look for a TASK tag near this complexity tag (within 200 chars)
        search_window = text[match.start():match.start() + 200]
        task_match = TASK_RE.search(search_window)
        description = task_match.group(1) if task_match else "(no description)"

        domain_match = re.search(r"DOMAIN:\s*([A-Za-z0-9_-]+)", search_window, re.IGNORECASE)
        domain = domain_match.group(1).upper() if domain_match else "SYSTEM"

        base_profile = PROFILES["sprinter"] if complexity == "LOW" else PROFILES["heavy_lifter"]
        
        from dataclasses import replace
        profile = replace(base_profile)
        
        # Domain parsing logic
        if domain in ("OSINT", "RAG"):
            pass  # keep base models (qwen2.5:7b or 32b)
        elif domain in ("CODE", "SYSTEM"):
            # Swap to coder family where appropriate
            if "7b" in profile.model:
                profile.model = profile.model.replace("qwen2.5:7b", "qwen2.5-coder:7b")

        tasks.append(RoutedTask(
            description=description,
            complexity=complexity,
            profile=profile,
            source_file=str(filepath),
        ))

    # --- Parse HTML comment annotations (<!-- COMPLEXITY: ... -->) ---
    lines = text.splitlines()
    for i, line in enumerate(lines):
        comment_match = COMMENT_COMPLEXITY_RE.search(line)
        if comment_match:
            complexity = comment_match.group(1).upper()
            # Use the line content (minus the comment) as the task description
            clean_line = COMMENT_COMPLEXITY_RE.sub("", line).strip()
            clean_line = re.sub(r"^-\s*\[.\]\s*", "", clean_line).strip()
            description = clean_line or f"(task at line {i + 1})"

            domain_match = re.search(r"DOMAIN:\s*([A-Za-z0-9_-]+)", line, re.IGNORECASE)
            domain = domain_match.group(1).upper() if domain_match else "SYSTEM"

            base_profile = PROFILES["sprinter"] if complexity == "LOW" else PROFILES["heavy_lifter"]
            from dataclasses import replace
            profile = replace(base_profile)
            
            # Domain parsing logic
            if domain in ("OSINT", "RAG"):
                pass
            elif domain in ("CODE", "SYSTEM"):
                if "7b" in profile.model:
                    profile.model = profile.model.replace("qwen2.5:7b", "qwen2.5-coder:7b")

            tasks.append(RoutedTask(
                description=description,
                complexity=complexity,
                profile=profile,
                source_file=str(filepath),
            ))

    return tasks


def discover_tasks() -> list[RoutedTask]:
    """
    Discover all routable tasks from:
      1. TASK_COMPLEXITY.md (primary)
      2. STATE_SYNC.md (inline comment tags)
      3. Any .md file in 00_MISSION_CONTROL/
    """
    all_tasks: list[RoutedTask] = []

    # Primary source
    all_tasks.extend(parse_complexity_from_file(TASK_COMPLEXITY_PATH))

    # STATE_SYNC inline tags
    all_tasks.extend(parse_complexity_from_file(STATE_SYNC_PATH))

    # Mission control docs
    if MISSION_CONTROL_DIR.exists():
        for md_file in MISSION_CONTROL_DIR.glob("*.md"):
            all_tasks.extend(parse_complexity_from_file(md_file))

    return all_tasks

# ---------------------------------------------------------------------------
# Ollama Interface (requests-based, fail-closed)
# ---------------------------------------------------------------------------

OLLAMA_TIMEOUT = 120  # seconds — strict timeout for all Ollama API calls
EXECUTION_OUTPUT = REPO_ROOT / "08_IMPLEMENTATION_NOTES" / "LATEST_EXECUTION_PROPOSAL.md"


def _fail_closed(reason: str) -> None:
    """Emit FAIL-CLOSED diagnostic and terminate. (LAW 1.4)"""
    log.critical(f"FAIL-CLOSED: {reason}")
    sys.exit(1)


def check_ollama_status() -> bool:
    """Ping Ollama /api/tags. Returns True if reachable, False otherwise."""
    if requests is None:
        log.warning("'requests' library not installed. Ollama unavailable.")
        return False
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def list_available_models() -> list[str]:
    """Query Ollama for locally available models."""
    if requests is None:
        return []
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def route_to_ollama(task: RoutedTask, prompt: Optional[str] = None) -> dict:
    """
    Route a task to the appropriate Ollama model.
    Returns the model response or a dry-run summary.
    """
    profile = task.profile
    if prompt is None:
        # Dry-run: just report the routing decision
        return {
            "mode": "dry_run",
            "task": task.description,
            "complexity": task.complexity,
            "routed_to": profile.name,
            "model": profile.model,
            "gpu_layers": profile.gpu_layers,
        }

    # Live inference via Ollama API (requests-based, fail-closed)
    if requests is None:
        _fail_closed("'requests' library not installed — cannot reach Ollama.")

    payload = {
        "model": profile.model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": profile.temperature,
            "num_predict": profile.max_tokens,
            "num_ctx": profile.context_window,
            "num_gpu": profile.gpu_layers,
        },
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"Ollama returned HTTP {resp.status_code}", "body": resp.text}
    except requests.Timeout:
        return {"error": f"Ollama inference timed out ({OLLAMA_TIMEOUT}s)"}
    except requests.ConnectionError:
        return {"error": "Ollama connection lost during inference."}
    except Exception as e:
        return {"error": str(e)}


def execute_task(model: str, task: str) -> None:
    """
    Execute a routed task against Ollama with fail-closed constraints.

    1. Ping /api/tags — if unreachable, FAIL-CLOSED.
    2. POST to /api/generate with timeout=120.
    3. Write provenance header + response to LATEST_EXECUTION_PROPOSAL.md.
    4. NEVER overwrites .py files, modifies directories, or executes shell commands.
    """
    if requests is None:
        _fail_closed("'requests' library not installed — cannot reach Ollama.")

    # Step 1: FAIL-CLOSED ping check
    log.info("Pinging Ollama at /api/tags...")
    if not check_ollama_status():
        _fail_closed("Ollama unavailable")

    # Step 2: Send inference request
    log.info(f"Sending task to model '{model}' (timeout={OLLAMA_TIMEOUT}s)...")
    payload = {
        "model": model,
        "prompt": task,
        "stream": False,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
    except requests.Timeout:
        _fail_closed(f"Ollama inference timed out ({OLLAMA_TIMEOUT}s). Model: {model}")
    except requests.ConnectionError:
        _fail_closed("Ollama connection lost during inference.")

    if resp.status_code != 200:
        _fail_closed(f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}")

    # Step 3: Extract response
    response_text = resp.json().get("response", "(no response from model)")

    # Step 4: Construct provenance header
    timestamp = datetime.datetime.utcnow().isoformat()
    provenance = (
        f"### MODEL: {model}\n"
        f"### TASK: {task}\n"
        f"### TIMESTAMP (UTC): {timestamp}\n"
        f"---\n\n"
    )

    # Step 5: Write to LATEST_EXECUTION_PROPOSAL.md
    EXECUTION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EXECUTION_OUTPUT.write_text(provenance + response_text, encoding="utf-8")
    log.info(f"✅ Proposal written to: {EXECUTION_OUTPUT}")
    log.info(f"   Model: {model} | Timestamp: {timestamp}")

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def print_routing_table(tasks: list[RoutedTask]) -> None:
    """Pretty-print the routing decisions."""
    if not tasks:
        log.info("No tasks found with COMPLEXITY tags.")
        return

    print("\n" + "=" * 72)
    print("  FIDUCIARY ZEROCLAW — SEMANTIC ROUTING TABLE")
    print("=" * 72)

    for i, task in enumerate(tasks, 1):
        icon = "⚡" if task.complexity == "LOW" else "🧠"
        print(f"\n  {icon}  Task #{i}")
        print(f"     Description : {task.description}")
        print(f"     Complexity  : {task.complexity}")
        print(f"     Profile     : {task.profile.name} ({task.profile.model})")
        print(f"     GPU Layers  : {task.profile.gpu_layers} ({'full GPU' if task.profile.gpu_layers == -1 else 'CPU offload'})")
        print(f"     Source      : {task.source_file}")

    print("\n" + "-" * 72)
    low_count = sum(1 for t in tasks if t.complexity == "LOW")
    high_count = sum(1 for t in tasks if t.complexity == "HIGH")
    print(f"  Summary: {low_count} Sprinter tasks | {high_count} Heavy Lifter tasks")
    print("=" * 72 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fiduciary ZeroClaw Semantic Router")
    parser.add_argument("--execute", nargs=2, metavar=("MODEL", "TASK"),
                        help="Execute a task against Ollama (fail-closed mode)")
    args = parser.parse_args()

    log.info("Semantic Router initializing...")
    log.info(f"Repo root: {REPO_ROOT}")

    # Execution mode: route directly to Ollama with fail-closed constraints
    if args.execute:
        model, task_desc = args.execute
        execute_task(model, task_desc)
        return 0

    # Discovery mode: scan, route, and display
    if check_ollama_status():
        models = list_available_models()
        log.info(f"Ollama online. Available models: {models}")
    else:
        log.warning("Ollama is not running. Routing will be dry-run only.")

    tasks = discover_tasks()
    log.info(f"Discovered {len(tasks)} routable task(s).")

    print_routing_table(tasks)

    for task in tasks:
        result = route_to_ollama(task)
        log.info(f"Route decision: {json.dumps(result, indent=2)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
