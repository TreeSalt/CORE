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
TIMEOUT           = 7200 # 2 Hours — allow deep reasoning headroom for 32b on limited VRAM

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

def select_tier(domain: dict, mission_text: str) -> tuple[str, str]:
    """
    Returns (tier_name, model_to_use) based on routing intelligence.
    Priority order:
    1. primary_tier from DOMAINS.yaml is the DEFAULT authority
    2. escalation_trigger == always_heavy OVERRIDES to heavy
    3. token_count > threshold ESCALATES to heavy (but only if primary is sprinter)
    """
    primary = domain.get("primary_tier", "sprinter")
    token_count = estimate_token_count(mission_text)
    token_threshold = domain.get("token_threshold", 2048)
    escalation = domain.get("escalation_trigger", "")

    # Forced heavy — domain config says always heavy (e.g. trading physics)
    if escalation == "always_heavy":
        return "heavy", domain["heavy_model"]

    # Token escalation — long mission bumps sprinter to heavy
    if primary == "sprinter" and token_count > token_threshold:
        log.info(f"Token escalation: {token_count} tokens > threshold {token_threshold}")
        return "heavy", domain["heavy_model"]

    # Default — respect the domain's primary tier
    if primary == "heavy":
        return "heavy", domain["heavy_model"]
    return "sprinter", domain["sprinter_model"]

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
    return (
        f"DOMAIN: {domain['id']}\n"
        f"SECURITY_CLASS: {domain.get('security_class', 'INTERNAL')}\n"
        f"MISSION: {mission}\n"
        f"TASK: {task}\n"
        f"CONSTRAINTS:\n"
        f"  - Proposals only. No direct execution.\n"
        f"  - No writes to 04_GOVERNANCE/\n"
        f"  - No hardcoded credentials\n"
        f"  - Fail closed on any constraint breach\n"
        f"  - Output valid Python code only\n"
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
        options = {"num_gpu": 0} if tier == "heavy" else {}

        res = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": context,
                "stream": False,
                "options": options
            },
            timeout=TIMEOUT
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
    tier, model = select_tier(domain, mission)

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
