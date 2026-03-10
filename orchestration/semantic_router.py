#!/usr/bin/env python3
"""
semantic_router.py — AOS Orchestration Engine
Version:        2.0.0
Constitution:   BOUND
Authors:        Supreme Council — TRADER_OPS
"""

import sys
import json
import hashlib
import logging
import requests
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import NoReturn

# ── PATHS (Surgically aligned to v9e_stage) ──────────────
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
TIMEOUT           = 120

# ── LOGGING ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
log = logging.getLogger("semantic_router")

_operator = {}
_domains  = {}

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

def verify_constitutional_hashes():
    log.info("Gate 1: Verifying constitutional hashes...")
    if not GOVERNOR_SEAL.exists(): _fail_closed("GOVERNOR_SEAL_MISSING")
    stored = {}
    for line in GOVERNOR_SEAL.read_text().splitlines():
        if line.startswith("AEC_HASH:"): stored["aec"] = line.split(":", 1)[1].strip()
        elif line.startswith("OI_HASH:"): stored["oi"] = line.split(":", 1)[1].strip()
    
    if "aec" not in stored or "oi" not in stored: _fail_closed("GOVERNOR_SEAL_MALFORMED")
    if _sha256(CONSTITUTION_FILE) != stored["aec"]: _fail_closed("CONSTITUTIONAL_INTEGRITY_BREACH (AEC)")
    if _sha256(OPERATOR_INSTANCE) != stored["oi"]: _fail_closed("CONSTITUTIONAL_INTEGRITY_BREACH (OI)")
    log.info("Gate 1: PASSED")

def load_operator_instance():
    global _operator
    log.info("Gate 2: Loading OPERATOR_INSTANCE.yaml...")
    with open(OPERATOR_INSTANCE, "r") as f: _operator = yaml.safe_load(f)
    if "{{" in OPERATOR_INSTANCE.read_text(): _fail_closed("OPERATOR_INSTANCE_INCOMPLETE")
    log.info("Gate 2: PASSED")

def load_domains_registry():
    global _domains
    log.info("Gate 3: Loading DOMAINS.yaml...")
    with open(DOMAINS_REGISTRY, "r") as f: _domains = {d["id"]: d for d in yaml.safe_load(f)["domains"]}
    log.info("Gate 3: PASSED")

def verify_ollama_status():
    log.info("Gate 4: Pinging Ollama...")
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10).raise_for_status()
        log.info("Gate 4: PASSED")
    except Exception as e:
        _fail_closed(f"OLLAMA_UNREACHABLE: {e}")

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

def update_vram_log(domain_id, model, status, proposal_path=""):
    now = datetime.now(timezone.utc).isoformat()
    entry = {"domain_id": domain_id, "model": model, "status": status, "completed_at": now, "proposal_path": proposal_path}
    try:
        state = json.load(open(VRAM_STATE_FILE)) if VRAM_STATE_FILE.exists() else {"session_history": []}
        state["last_updated"] = now
        state["last_task"] = entry
        state["session_history"].append(entry)
        with open(VRAM_STATE_FILE, "w") as f: json.dump(state, f, indent=2)
    except Exception:
        pass

def load_mission_prompt(mission_file: str) -> str:
    path = Path(mission_file) if Path(mission_file).is_absolute() else MISSIONS_DIR / mission_file
    if not path.exists(): _fail_closed(f"MISSION_PROMPT_MISSING: {path}")
    log.info("Gate 5: PASSED")
    return path.read_text().strip()

def _build_context_package(domain, task, mission):
    return (f"DOMAIN: {domain['id']}\nMISSION: {mission}\nTASK: {task}\n"
            f"CONSTRAINTS: Respect boundaries. Proposal format only.")

def write_proposal(domain_id, model, pilot, content, mission_file):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    proposal_path = PROPOSALS_DIR / f"PROPOSAL_{domain_id}_{timestamp}.md"
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(f"---\nDOMAIN: {domain_id}\nSTATUS: PENDING_REVIEW\n---\n\n{content}")
    log.info(f"Proposal written: {proposal_path.name}")
    return proposal_path

def execute_local(domain, task, mission):
    model, domain_id = domain["worker"], domain["id"]
    context = _build_context_package(domain, task, mission)
    update_vram_log(domain_id, model, "ACTIVE")
    log.info(f"Executing LOCAL: {model}")
    try:
        res = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": model, "prompt": context, "stream": False}, timeout=TIMEOUT)
        res.raise_for_status()
        content = res.json().get("response", "")
        proposal_path = write_proposal(domain_id, model, "local", content, mission)
        update_vram_log(domain_id, model, "COMPLETE", str(proposal_path))
        return proposal_path
    except Exception as e:
        _fail_closed(f"EXECUTION_FAILED: {e}")

def execute_cloud(domain, task, mission):
    domain_id = domain["id"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    pending_file = PENDING_DIR / f"PENDING_{domain_id}_{timestamp}.md"
    context = _build_context_package(domain, task, mission)
    pending_file.write_text(f"# CLOUD TASK\n{context}\n\nINSTRUCTIONS: Execute in Claude Code terminal.")
    log.info(f"\n{'='*60}\nCLOUD TASK PACKAGED: {pending_file}\nOpen Claude Code terminal and run: claude < {pending_file}\n{'='*60}")
    return pending_file

def route_task(domain_id, task, mission_file):
    if domain_id not in _domains: _fail_closed("DOMAIN_NOT_FOUND")
    if _domains[domain_id]["pilot"] == "HUMAN_SOVEREIGN": _fail_closed("SOVEREIGNTY_VIOLATION")
    mission = load_mission_prompt(mission_file)
    if not check_vram_ceiling(): _fail_closed("HARDWARE_CEILING_BREACH")
    
    pilot = _domains[domain_id]["pilot"]
    return execute_local(_domains[domain_id], task, mission) if pilot == "local" else execute_cloud(_domains[domain_id], task, mission)

def initialize():
    log.info("AOS SEMANTIC ROUTER v2.0.0 — INITIALIZING")
    verify_constitutional_hashes()
    load_operator_instance()
    load_domains_registry()
    verify_ollama_status()
    log.info("ALL GATES PASSED — ROUTER ONLINE")

initialize()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--mission", required=True)
    args = parser.parse_args()
    print(f"\nProposal ready: {route_task(args.domain, args.task, args.mission)}")
