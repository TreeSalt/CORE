#!/usr/bin/env python3
"""
SOVEREIGN PATCH — Fix ARCHITECTURE proposal routing
====================================================
DECISION-SOVEREIGN-003: Strategic ARCHITECTURE proposals must not be
downgraded to sprinter. The downgrade was appropriate for CODE_ARCHITECTURE
(avoiding 15min timeouts on boilerplate) but catastrophically wrong for
STRATEGIC_ARCHITECTURE (Zoo blueprints, domain design).

Fix 1: orchestration/semantic_router.py
  - Add STRATEGIC_ARCHITECTURE type that never downgrades
  - Only downgrade CODE_ARCHITECTURE to sprinter

Fix 2: 04_GOVERNANCE/DOMAINS.yaml
  - 00_PHYSICS_ENGINE: primary_tier sprinter → heavy, add always_heavy

Fix 3: orchestration/MISSION_QUEUE.json
  - Zoo mission: type ARCHITECTURE → STRATEGIC_ARCHITECTURE
"""
from pathlib import Path
import json

REPO_ROOT = Path(".")

# ── FIX 1: semantic_router.py ─────────────────────────────────────────────────
router = REPO_ROOT / "orchestration" / "semantic_router.py"
content = router.read_text()

old = '''    # ARCHITECTURE blueprints don't need heavy model reasoning — downgrade to sprinter
    if proposal_type == "ARCHITECTURE" and tier == "heavy":
        model = domain.get("sprinter_model", model)
        tier  = "sprinter"
        log.info(f"ARCHITECTURE proposal — downgraded to sprinter: {model}")'''

new = '''    # CODE_ARCHITECTURE blueprints downgrade to sprinter (avoid timeout on boilerplate)
    # STRATEGIC_ARCHITECTURE (Zoo blueprints, domain design) NEVER downgrades — 32b required
    if proposal_type == "ARCHITECTURE" and tier == "heavy":
        model = domain.get("sprinter_model", model)
        tier  = "sprinter"
        log.info(f"CODE_ARCHITECTURE proposal — downgraded to sprinter: {model}")
    elif proposal_type == "STRATEGIC_ARCHITECTURE":
        # Never downgrade — strategic content requires 32b reasoning
        log.info(f"STRATEGIC_ARCHITECTURE proposal — maintaining heavy tier: {model}")'''

if old in content:
    router.write_text(content.replace(old, new))
    print("✅ Fix 1: semantic_router.py patched — STRATEGIC_ARCHITECTURE routing added")
else:
    print("❌ Fix 1: Pattern not found in semantic_router.py — manual patch required")
    print("   Look for 'ARCHITECTURE blueprints don't need heavy' in execute_local()")

# ── FIX 2: DOMAINS.yaml ───────────────────────────────────────────────────────
domains_file = REPO_ROOT / "04_GOVERNANCE" / "DOMAINS.yaml"
domains_content = domains_file.read_text()

old_physics = '''  - id: "00_PHYSICS_ENGINE"
    description: "Core trading physics, signal mathematics, SMA/EMA/deque engine"
    security_class: "CONFIDENTIAL"
    cloud_eligible: false
    primary_tier: "sprinter"
    sprinter_model: "qwen2.5-coder:7b"
    heavy_model: "qwen2.5-coder:32b"
    complexity: "HIGH"
    token_threshold: 2048
    write_path: "00_PHYSICS_ENGINE/"
    authorized_agents: ["qwen2.5-coder:7b", "qwen2.5-coder:32b"]
    escalation_trigger: "complexity==HIGH or token_count>token_threshold"'''

new_physics = '''  - id: "00_PHYSICS_ENGINE"
    description: "Core trading physics, signal mathematics, SMA/EMA/deque engine. Zoo strategy architecture."
    security_class: "CONFIDENTIAL"
    cloud_eligible: false
    primary_tier: "heavy"
    sprinter_model: "qwen2.5-coder:7b"
    heavy_model: "qwen2.5-coder:32b"
    complexity: "HIGH"
    token_threshold: 2048
    write_path: "00_PHYSICS_ENGINE/"
    authorized_agents: ["qwen2.5-coder:7b", "qwen2.5-coder:32b"]
    escalation_trigger: "always_heavy"
    note: "Zoo strategy blueprints are high-stakes strategic architecture. Always heavy."'''

if old_physics in domains_content:
    domains_file.write_text(domains_content.replace(old_physics, new_physics))
    print("✅ Fix 2: DOMAINS.yaml patched — 00_PHYSICS_ENGINE escalated to always_heavy")
else:
    print("❌ Fix 2: Pattern not found in DOMAINS.yaml — manual patch required")

# ── FIX 3: MISSION_QUEUE.json ─────────────────────────────────────────────────
queue_file = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
queue = json.loads(queue_file.read_text())

for m in queue["missions"]:
    if m["id"] == "zoo_epoch1_strategy_variants_001":
        m["type"] = "STRATEGIC_ARCHITECTURE"
        m["status"] = "PENDING"
        m["rationale"] += " — REQUEUED as STRATEGIC_ARCHITECTURE after routing failure. 32b required."
        print(f"✅ Fix 3: Zoo mission requeued as STRATEGIC_ARCHITECTURE → 32b heavy lifter")

queue_file.write_text(json.dumps(queue, indent=2))

print("\nAll fixes applied. Next steps:")
print("1. python3 -c 'import hashlib,pathlib; ...' (reseal governor)")
print("2. git add orchestration/semantic_router.py 04_GOVERNANCE/DOMAINS.yaml orchestration/MISSION_QUEUE.json")
print("3. git commit -m 'fix: DECISION-SOVEREIGN-003 — strategic architecture routing'")
print("4. make reseal && make drop")
