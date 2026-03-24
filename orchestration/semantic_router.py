#!/usr/bin/env python3
"""
semantic_router.py — AOS Orchestration Engine
Version:        3.0.0
Constitution:   BOUND
Authors:        Supreme Council — TRADER_OPS

ROUTING INTELLIGENCE:
  1. Security gate    — CONFIDENTIAL/SOVEREIGN domains never leave local machine
  2. Secrets scan     — mission file scanned for credentials before any dispatch
  3. Tier selection   — task complexity + token count determines Sprinter vs Heavy Lifter
  4. VRAM check       — live hardware state gates local execution
  5. Cloud fallback   — if cloud unreachable and domain allows, fall back to local Heavy Lifter
  6. Dispatch         — execute with selected model, log decision
"""

import sys
import json
import hashlib
import logging
import re
import requests
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import NoReturn

# ── PATHS ─────────────────────────────────────────────────────────────────────
REPO_ROOT         = Path(__file__).resolve().parents[1]
GOVERNOR_SEAL     = REPO_ROOT / ".governor_seal"
OPERATOR_INSTANCE = REPO_ROOT / "04_GOVERNANCE" / "OPERATOR_INSTANCE.yaml"
DOMAINS_REGISTRY  = REPO_ROOT / "04_GOVERNANCE" / "DOMAINS.yaml"
CONSTITUTION_FILE = REPO_ROOT / "04_GOVERNANCE" / "AGENTIC_ETHICAL_CONSTITUTION.md"
VRAM_STATE_FILE   = REPO_ROOT / "orchestration" / "VRAM_STATE.json"
ERROR_LEDGER      = REPO_ROOT / "docs" / "ERROR_LEDGER.md"
PROPOSALS_DIR     = REPO_ROOT / "08_IMPLEMENTATION_NOTES"
MISSIONS_DIR      = REPO_ROOT / "prompts" / "missions"
PENDING_DIR       = MISSIONS_DIR / "PENDING"

OLLAMA_BASE_URL   = "http://localhost:11434"
TIMEOUT           = 600  # 10 min — 9B on GPU completes in 3-7 min. VRAM gate prevents 27B dispatch on 8GB cards

# ── SECRETS PATTERNS (mission file scan) ──────────────────────────────────────
SECRET_PATTERNS = [
    r'(?i)(password|passwd|pwd)\s*=\s*["\']?\S+',
    r'(?i)(api_key|apikey|api-key)\s*=\s*["\']?\S+',
    r'(?i)(secret|token|auth)\s*=\s*["\']?\S+',
    r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*',
    r'[A-Za-z0-9]{32,}',  # Long opaque strings (potential tokens)
]

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
log = logging.getLogger("semantic_router")

_operator = {}
_domains  = {}

# ── CORE UTILITIES ────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _fail_closed(reason: str) -> NoReturn:
    timestamp = datetime.now(timezone.utc).isoformat()
    log.critical(f"FAIL-CLOSED: {reason}")
    ERROR_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ERROR_LEDGER, "a") as f:
            f.write(f"\n### {timestamp} — FAIL-CLOSED\n**Reason:** {reason}\n**Recovery:** Human Supreme Council action required.\n")
    except Exception:
        pass
    sys.exit(1)

def _log_routing_decision(domain_id, model, tier, reason):
    log.info(f"ROUTING DECISION: domain={domain_id} model={model} tier={tier} reason={reason}")
    try:
        state = json.load(open(VRAM_STATE_FILE)) if VRAM_STATE_FILE.exists() else {"routing_log": []}
        state.setdefault("routing_log", []).append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain_id": domain_id,
            "model": model,
            "tier": tier,
            "reason": reason
        })
        with open(VRAM_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

# ── STARTUP GATES ─────────────────────────────────────────────────────────────

def verify_constitutional_hashes():
    log.info("Gate 1: Verifying constitutional hashes...")
    if not GOVERNOR_SEAL.exists():
        _fail_closed("GOVERNOR_SEAL_MISSING")
    stored = {}
    for line in GOVERNOR_SEAL.read_text().splitlines():
        if line.startswith("AEC_HASH:"):
            stored["aec"] = line.split(":", 1)[1].strip()
        elif line.startswith("OI_HASH:"):
            stored["oi"] = line.split(":", 1)[1].strip()
    if "aec" not in stored or "oi" not in stored:
        _fail_closed("GOVERNOR_SEAL_MALFORMED")
    if _sha256(CONSTITUTION_FILE) != stored["aec"]:
        _fail_closed("CONSTITUTIONAL_INTEGRITY_BREACH (AEC)")
    if _sha256(OPERATOR_INSTANCE) != stored["oi"]:
        _fail_closed("CONSTITUTIONAL_INTEGRITY_BREACH (OI)")
    log.info("Gate 1: PASSED")

def load_operator_instance():
    global _operator
    log.info("Gate 2: Loading OPERATOR_INSTANCE.yaml...")
    with open(OPERATOR_INSTANCE, "r") as f:
        _operator = yaml.safe_load(f)
    if "{{" in OPERATOR_INSTANCE.read_text():
        _fail_closed("OPERATOR_INSTANCE_INCOMPLETE")
    log.info("Gate 2: PASSED")

def load_domains_registry():
    global _domains
    log.info("Gate 3: Loading DOMAINS.yaml...")
    with open(DOMAINS_REGISTRY, "r") as f:
        _domains = {d["id"]: d for d in yaml.safe_load(f)["domains"]}
    log.info("Gate 3: PASSED")

def verify_ollama_status():
    log.info("Gate 4: Pinging Ollama...")
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10).raise_for_status()
        log.info("Gate 4: PASSED")
    except Exception as e:
        _fail_closed(f"OLLAMA_UNREACHABLE: {e}")

# ── ROUTING INTELLIGENCE ──────────────────────────────────────────────────────

def scan_for_secrets(text: str, source: str = "mission"):
    """Gate: Fail closed if mission file contains credentials or tokens."""
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            _fail_closed(f"SECRETS_DETECTED_IN_{source.upper()}: Pattern matched — refusing dispatch. Remove credentials before routing.")

def check_security_class(domain: dict) -> str:
    """Returns security class. SOVEREIGN/CONFIDENTIAL = local only."""
    sec = domain.get("security_class", "INTERNAL")
    if sec == "SOVEREIGN":
        _fail_closed(f"SOVEREIGNTY_VIOLATION: Domain {domain['id']} is SOVEREIGN. No agent dispatch permitted.")
    if sec == "CONFIDENTIAL" and domain.get("cloud_eligible", False):
        _fail_closed(f"SECURITY_MISCONFIGURATION: Domain {domain['id']} is CONFIDENTIAL but marked cloud_eligible. Fix DOMAINS.yaml.")
    return sec

def estimate_token_count(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4

def _query_model_size_mb(model_name: str) -> int:
    """Query Ollama API for the actual on-disk size of a model in MB."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                return int(m["size"] / (1024 * 1024))
    except Exception as e:
        log.warning(f"Could not query model size for {model_name}: {e}")
    return 0


def _query_available_memory_mb() -> tuple[int, int]:
    """Query actual free VRAM and system RAM in MB. Returns (vram_mb, ram_mb)."""
    free_vram = 0
    free_ram = 0
    try:
        import subprocess as _sp
        _r = _sp.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                     capture_output=True, text=True, timeout=5)
        free_vram = int(_r.stdout.strip().split("\n")[0])
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    free_ram = int(line.split()[1]) // 1024
                    break
    except Exception:
        pass
    return free_vram, free_ram


def _classify_model_tier(model_name: str) -> str:
    """Classify a model into sprinter/cruiser/heavy based on Ollama metadata."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                param_str = m["details"].get("parameter_size", "0B")
                param_val = float(param_str.replace("B", "").strip())
                if param_val < 9:
                    return "sprinter"
                elif param_val < 24:
                    return "cruiser"
                else:
                    return "heavy"
    except Exception as e:
        log.warning(f"Could not classify {model_name}: {e}")
    return "sprinter"


def _query_model_size_mb(model_name: str) -> int:
    """Query Ollama API for the actual on-disk size of a model in MB."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                return int(m["size"] / (1024 * 1024))
    except Exception as e:
        log.warning(f"Could not query model size for {model_name}: {e}")
    return 0


def _query_available_memory_mb() -> tuple[int, int]:
    """Query actual free VRAM and system RAM in MB. Returns (vram_mb, ram_mb)."""
    free_vram = 0
    free_ram = 0
    try:
        import subprocess as _sp
        _r = _sp.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        free_vram = int(_r.stdout.strip().split(chr(10))[0])
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    free_ram = int(line.split()[1]) // 1024
                    break
    except Exception:
        pass
    return free_vram, free_ram


def _classify_model_tier(model_name: str) -> str:
    """Classify a model into sprinter/cruiser/heavy based on Ollama metadata."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                param_str = m["details"].get("parameter_size", "0B")
                param_val = float(param_str.replace("B", "").strip())
                if param_val < 9:
                    return "sprinter"
                elif param_val < 24:
                    return "cruiser"
                else:
                    return "heavy"
    except Exception as e:
        log.warning(f"Could not classify {model_name}: {e}")
    return "sprinter"


def _query_model_size_mb(model_name: str) -> int:
    """Query Ollama API for the actual on-disk size of a model in MB."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                return int(m["size"] / (1024 * 1024))
    except Exception as e:
        log.warning(f"Could not query model size for {model_name}: {e}")
    return 0


def _query_available_memory_mb() -> tuple[int, int]:
    """Query actual free VRAM and system RAM in MB. Returns (vram_mb, ram_mb)."""
    free_vram = 0
    free_ram = 0
    try:
        import subprocess as _sp
        _r = _sp.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        free_vram = int(_r.stdout.strip().split(chr(10))[0])
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    free_ram = int(line.split()[1]) // 1024
                    break
    except Exception:
        pass
    return free_vram, free_ram


def _classify_model_tier(model_name: str) -> str:
    """Classify a model into sprinter/cruiser/heavy based on Ollama metadata."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        for m in resp.json().get("models", []):
            if m["name"] == model_name:
                param_str = m["details"].get("parameter_size", "0B")
                param_val = float(param_str.replace("B", "").strip())
                if param_val < 9:
                    return "sprinter"
                elif param_val < 24:
                    return "cruiser"
                else:
                    return "heavy"
    except Exception as e:
        log.warning(f"Could not classify {model_name}: {e}")
    return "sprinter"


def select_tier(domain: dict, mission_text: str) -> tuple[str, str]:
    """
    Hardware-relative, model-aware tier selection.

    Three-tier hierarchy (operator-tunable via DOMAINS.yaml):
      Sprinter (<9B params)  -- fast, light tasks
      Cruiser  (9-24B params) -- complex logic, API adapters
      Heavy    (24B+ params)  -- strategic architecture, deep reasoning

    Memory gate queries Ollama for actual model sizes and the OS for real
    VRAM + system RAM. Ollama supports partial GPU offloading, so models
    larger than VRAM can split across VRAM+RAM (slower but correct).

    Degradation ladder: heavy -> cruiser -> sprinter.
    If always_heavy cannot fit in combined memory, returns ("ESCALATE", "").
    """
    primary = domain.get("primary_tier", "sprinter")
    token_count = estimate_token_count(mission_text)
    token_threshold = domain.get("token_threshold", 2048)
    escalation = domain.get("escalation_trigger", "")

    if escalation == "always_heavy":
        desired_tier = "heavy"
    elif primary == "heavy":
        desired_tier = "heavy"
    elif primary == "cruiser":
        desired_tier = "cruiser"
    elif primary == "sprinter" and token_count > token_threshold:
        log.info(f"Token escalation: {token_count} > threshold {token_threshold}")
        desired_tier = "cruiser"
    else:
        desired_tier = "sprinter"

    TIER_LADDER = [
        ("heavy", "heavy_model"),
        ("cruiser", "cruiser_model"),
        ("sprinter", "sprinter_model"),
    ]

    free_vram, free_ram = _query_available_memory_mb()
    total_available = free_vram + free_ram
    log.info(f"MEMORY GATE: VRAM={free_vram}MB, RAM={free_ram}MB, total={total_available}MB")

    start_idx = next(
        (i for i, (t, _) in enumerate(TIER_LADDER) if t == desired_tier), 0
    )
    selected_tier = None
    selected_model = None
    memory_mode = "VRAM"

    for tier_name, model_key in TIER_LADDER[start_idx:]:
        model_name = domain.get(model_key)
        if not model_name:
            continue

        required_mb = _query_model_size_mb(model_name)
        if required_mb == 0:
            log.warning(f"MEMORY GATE: {model_name} not found in Ollama, skipping")
            continue

        if required_mb <= free_vram:
            selected_tier = tier_name
            selected_model = model_name
            memory_mode = "VRAM"
            log.info(
                f"MEMORY GATE: {model_name} fits in VRAM "
                f"({required_mb}MB <= {free_vram}MB)"
            )
            break
        elif required_mb <= total_available:
            selected_tier = tier_name
            selected_model = model_name
            memory_mode = "SPLIT"
            log.warning(
                f"MEMORY GATE: {model_name} will SPLIT across VRAM+RAM "
                f"({required_mb}MB needed, {free_vram}MB VRAM + {free_ram}MB RAM). "
                f"Inference will be slower."
            )
            break
        else:
            log.info(
                f"MEMORY GATE: {model_name} too large "
                f"({required_mb}MB > {total_available}MB available), trying next tier"
            )

    if selected_tier is None:
        if escalation == "always_heavy":
            log.error(
                f"MEMORY GATE: ESCALATE -- {domain['id']} requires always_heavy "
                f"but no model fits in available memory ({total_available}MB). "
                f"Sovereign intervention required."
            )
            return "ESCALATE", ""
        for _, model_key in reversed(TIER_LADDER):
            fallback = domain.get(model_key)
            if fallback:
                selected_tier = "sprinter"
                selected_model = fallback
                log.warning(
                    f"MEMORY GATE: All tiers exceeded. Last resort: {fallback}"
                )
                break

    if selected_tier and selected_tier != desired_tier:
        log.warning(
            f"TIER DEGRADED: {domain['id']} wanted {desired_tier} but dispatching "
            f"{selected_tier} ({selected_model}). Output quality may be reduced."
        )
        _log_routing_decision(
            domain["id"], selected_model, selected_tier,
            f"Degraded from {desired_tier}: memory constraint ({memory_mode})",
        )

    recommended_timeout = 1800 if memory_mode == "SPLIT" else 600
    return selected_tier, selected_model, recommended_timeout

def get_live_vram_state() -> dict:
    try:
        models = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=10).json().get("models", [])
        return {"loaded_models": [m["name"] for m in models], "count": len(models)}
    except Exception as e:
        _fail_closed(f"VRAM_STATE_UNREADABLE: {e}")

def check_vram_ceiling() -> bool:
    ceiling = _operator["hardware"]["ollama_max_loaded_models"]
    live = get_live_vram_state()
    if live["count"] >= ceiling:
        log.warning(f"VRAM ceiling reached: {live['count']}/{ceiling} models loaded.")
        return False
    return True

def check_cloud_reachable() -> bool:
    """Lightweight check — can we reach the internet?"""
    try:
        requests.get("https://api.anthropic.com", timeout=5)
        return True
    except Exception:
        log.warning("Cloud unreachable — falling back to local Heavy Lifter if domain allows.")
        return False

def update_vram_log(domain_id, model, status, proposal_path=""):
    now = datetime.now(timezone.utc).isoformat()
    entry = {"domain_id": domain_id, "model": model, "status": status,
             "completed_at": now, "proposal_path": proposal_path}
    try:
        state = json.load(open(VRAM_STATE_FILE)) if VRAM_STATE_FILE.exists() else {"session_history": []}
        state["last_updated"] = now
        state["last_task"] = entry
        state.setdefault("session_history", []).append(entry)
        with open(VRAM_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def load_mission_prompt(mission_file: str) -> str:
    path = Path(mission_file) if Path(mission_file).is_absolute() else MISSIONS_DIR / mission_file
    if not path.exists():
        _fail_closed(f"MISSION_PROMPT_MISSING: {path}")
    text = path.read_text().strip()
    scan_for_secrets(text, source="mission")
    log.info("Gate 5: PASSED — mission loaded, secrets scan clean")
    return text

# ── EXECUTION ─────────────────────────────────────────────────────────────────

def _build_context_package(domain, task, mission):
    # Read the actual mission brief — this is the LLM's instructions
    mission_path = REPO_ROOT / "prompts" / "missions" / mission
    mission_content = ""
    if mission_path.exists():
        mission_content = mission_path.read_text()
    else:
        log.warning(f"Mission file not found: {mission_path}")

    return (
        f"DOMAIN: {domain['id']}\n"
        f"SECURITY_CLASS: {domain.get('security_class', 'INTERNAL')}\n"
        f"TASK: {task}\n"
        f"CONSTRAINTS:\n"
        f"  - Proposals only. No direct execution.\n"
        f"  - No writes to 04_GOVERNANCE/\n"
        f"  - No hardcoded credentials\n"
        f"  - Fail closed on any constraint breach\n"
        f"  - Output valid Python code only\n\n"
        f"--- MISSION BRIEF ---\n"
        f"{mission_content}\n"
    )

def write_proposal(domain_id, model, tier, proposal_type, content):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    proposal_path = PROPOSALS_DIR / f"PROPOSAL_{domain_id}_{timestamp}.md"
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(
        f"---\nDOMAIN: {domain_id}\nMODEL: {model}\nTIER: {tier}\nTYPE: {proposal_type}\nSTATUS: PENDING_REVIEW\n---\n\n{content}"
    )
    log.info(f"Proposal written: {proposal_path.name}")
    return proposal_path

def execute_local(domain, task, mission, tier, model, proposal_type="IMPLEMENTATION"):
    # CODE_ARCHITECTURE blueprints downgrade to sprinter (avoid timeout on boilerplate)
    # STRATEGIC_ARCHITECTURE (Zoo blueprints, domain design) NEVER downgrades — 32b required
    if proposal_type == "ARCHITECTURE" and tier == "heavy":
        model = domain.get("sprinter_model", model)
        tier  = "sprinter"
        log.info(f"CODE_ARCHITECTURE proposal — downgraded to sprinter: {model}")
    elif proposal_type == "STRATEGIC_ARCHITECTURE":
        # Never downgrade — strategic content requires 32b reasoning
        log.info(f"STRATEGIC_ARCHITECTURE proposal — maintaining heavy tier: {model}")
    domain_id = domain["id"]
    context = _build_context_package(domain, task, mission)
    _log_routing_decision(domain_id, model, tier, f"local execution — security_class={domain.get('security_class')}")
    update_vram_log(domain_id, model, "ACTIVE")
    log.info(f"Executing LOCAL [{tier.upper()}]: {model}")
    try:
        # Prepare options. num_gpu=0 forces the model to load into 
        # system RAM (32GB available), avoiding 8GB VRAM bottlenecks/crashes.
        options = {}  # VRAM gate in select_tier() handles GPU/CPU routing — no forced CPU override

        res = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": context,
                "stream": False,
                "options": options
            },
            timeout=1800 if "27b" in model or "30b" in model or "32b" in model or "35b" in model else 600
        )
        res.raise_for_status()
        content = res.json().get("response", "")
        proposal_path = write_proposal(domain_id, model, tier, proposal_type, content)
        update_vram_log(domain_id, model, "COMPLETE", str(proposal_path))
        return proposal_path
    except Exception as e:
        _fail_closed(f"LOCAL_EXECUTION_FAILED [{model}]: {e}")

def execute_cloud(domain, task, mission, tier, proposal_type="IMPLEMENTATION"):
    domain_id = domain["id"]
    cloud_model = domain.get("cloud_model", "claude-code")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    pending_file = PENDING_DIR / f"PENDING_{domain_id}_{timestamp}.md"
    context = _build_context_package(domain, task, mission)
    pending_file.write_text(
        f"# CLOUD TASK PACKAGE\n"
        f"# Model: {cloud_model} | Tier: {tier} | Domain: {domain_id}\n"
        f"# Security: {domain.get('security_class')} | Cloud-eligible: {domain.get('cloud_eligible')}\n\n"
        f"{context}\n\n"
        f"INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/."
    )
    _log_routing_decision(domain_id, cloud_model, tier, "cloud execution via file_handoff")
    log.info(f"\n{'='*60}\nCLOUD TASK PACKAGED [{tier.upper()}]: {pending_file}\nRun: claude < {pending_file}\n{'='*60}")
    return pending_file

# ── MAIN ROUTING LOGIC ────────────────────────────────────────────────────────

def route_task(domain_id, task, mission_file, proposal_type="IMPLEMENTATION"):
    if domain_id not in _domains:
        _fail_closed(f"DOMAIN_NOT_FOUND: {domain_id}")

    domain = _domains[domain_id]

    # Security gate — must run first, before any data leaves
    sec_class = check_security_class(domain)

    # Load and scan mission
    mission = load_mission_prompt(mission_file)

    # Tier selection based on complexity + token count
    tier, model, dynamic_timeout = select_tier(domain, mission)

    # VRAM ceiling check for local execution
    if not check_vram_ceiling():
        _fail_closed("HARDWARE_CEILING_BREACH — unload a model before dispatching")

    # LOCAL LOCKDOWN CHECK
    lockdown_file = Path(__file__).resolve().parent / "LOCAL_LOCKDOWN.json"
    if lockdown_file.exists():
        import json as _json
        lockdown = _json.loads(lockdown_file.read_text())
        if lockdown.get("enabled", False):
            log.warning(f"🔒 LOCAL LOCKDOWN ACTIVE — forcing local execution. Reason: {lockdown.get('reason', 'none')}")
            return execute_local(domain, task, mission, tier, model, proposal_type)

    # Cloud eligibility + reachability
    cloud_eligible = domain.get("cloud_eligible", False)

    if not cloud_eligible:
        # Must stay local — security policy
        log.info(f"Security policy: {domain_id} is {sec_class} — local only, no cloud dispatch")
        return execute_local(domain, task, mission, tier, model, proposal_type)

    # Cloud eligible — check reachability
    cloud_up = check_cloud_reachable()
    if cloud_up and tier == "heavy":
        # Complex cloud-eligible task — send to Claude Code
        log.info(f"Cloud dispatch: {domain_id} is cloud-eligible and task is heavy tier")
        return execute_cloud(domain, task, mission, tier, proposal_type)

    if not cloud_up and cloud_eligible:
        # Cloud down — fall back to local Heavy Lifter
        log.warning(f"Cloud unreachable — falling back to local heavy lifter: {domain['heavy_model']}")
        return execute_local(domain, task, mission, "heavy", domain["heavy_model"], proposal_type)

    # Default: local sprinter
    return execute_local(domain, task, mission, tier, model, proposal_type)

# ── INIT ──────────────────────────────────────────────────────────────────────

def initialize():
    log.info("AOS SEMANTIC ROUTER v3.0.0 — INITIALIZING")
    verify_constitutional_hashes()
    load_operator_instance()
    load_domains_registry()
    verify_ollama_status()
    log.info("ALL GATES PASSED — ROUTER ONLINE")

initialize()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AOS Semantic Router v3.0.0")
    parser.add_argument("--domain",  required=True, help="Domain ID from DOMAINS.yaml")
    parser.add_argument("--task",    required=True, help="Task identifier")
    parser.add_argument("--mission", required=True, help="Mission filename in prompts/missions/")
    parser.add_argument("--type", default="IMPLEMENTATION", choices=["IMPLEMENTATION", "ARCHITECTURE", "STRATEGIC_ARCHITECTURE"],
                        help="Proposal type hint: IMPLEMENTATION or ARCHITECTURE")
    args = parser.parse_args()
    result = route_task(args.domain, args.task, args.mission, args.type)
    print(f"\nProposal ready: {result}")
