#!/usr/bin/env python3
"""
FACTORY BATCH: DOMAINS Update + Career Infrastructure
"""
import json
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(".")
MISSIONS = REPO / "prompts" / "missions"
QUEUE = REPO / "orchestration" / "MISSION_QUEUE.json"
now = datetime.now(timezone.utc).isoformat()

missions_data = []

# Mission 1: DOMAINS.yaml Qwen 3.5 update
m1 = """# MISSION: Update DOMAINS.yaml — Qwen 3.5 Model Roster
DOMAIN: 03_ORCHESTRATION
TASK: update_domains_model_roster
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The sovereign has downloaded Qwen 3.5 models. The model roster in
DOMAINS.yaml and the semantic router must be updated to reflect the
new 4-tier hierarchy.

## BLUEPRINT
Update 04_GOVERNANCE/DOMAINS.yaml to reflect:

Tier FLASH: qwen3.5:4b (3.4 GB) — syntax checks, linting, simple routing
Tier SPRINT: qwen3.5:9b (6.6 GB) — code generation, mission routing
Tier HEAVY: qwen3.5:27b (17 GB) — strategy implementation, complex reasoning
  Alternate: qwen3-coder:30b (18 GB) for code-specific tasks
Tier SUPREME: qwen3.5:35b (23 GB) — architecture proposals, alpha synthesis
Tier COUNCIL: claude.ai — sovereign review, governance decisions

Also update the domain-to-tier mappings:
  00_PHYSICS_ENGINE: heavy (qwen3.5:27b or qwen3-coder:30b)
  01_DATA_INGESTION: sprint (qwen3.5:9b)
  02_RISK_MANAGEMENT: heavy (qwen3.5:27b)
  03_ORCHESTRATION: sprint (qwen3.5:9b)
  05_REPORTING: flash (qwen3.5:4b)
  06_BENCHMARKING: sprint (qwen3.5:9b)
  07_INTEGRATION: council (claude.ai)
  08_CYBERSECURITY: heavy (qwen3.5:27b)

Update orchestration/VRAM_STATE.json model sizes accordingly.

## DELIVERABLE
Patch to 04_GOVERNANCE/DOMAINS.yaml and orchestration/VRAM_STATE.json

## CONSTRAINTS
- Preserve existing domain security classifications
- Preserve cloud/local eligibility flags
- Output valid YAML only
"""

# Mission 2: Autoresearch-style program.md for AOS
m2 = """# MISSION: Create AOS program.md — Karpathy-Style Agent Instructions
DOMAIN: 03_ORCHESTRATION
TASK: implement_program_md
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Inspired by Karpathy's autoresearch project (33k GitHub stars), which uses
a single program.md file to carry instructions, constraints, and stopping
criteria for autonomous AI agents. Our mission files are similar but scattered.

## BLUEPRINT
Create a master 00_MISSION_CONTROL/PROGRAM.md that:
1. Describes the AOS in 60 seconds (what it is, what it does)
2. Lists the three primitives (editable asset, scalar metric, time budget)
3. Maps each domain to its editable assets and success metrics
4. Defines the experiment loop: propose → benchmark → gate → ratify/discard
5. Lists hard constraints (constitutional, never violated)
6. Lists stopping criteria (when to escalate vs continue)
7. References CHECKPOINTS.yaml for advancement gates

This is the document any AI agent reads FIRST when joining the project.
It replaces the need to read the entire repomix.

## DELIVERABLE
File: 00_MISSION_CONTROL/PROGRAM.md

## CONSTRAINTS
- Must be readable by any LLM in under 2000 tokens
- Must reference existing governance files by path
- ARCHITECTURE type — auto-ratifies
- Output valid markdown only
"""

# Mission 3: Portfolio showcase page data
m3 = """# MISSION: Project Metrics Exporter — Portfolio Data
DOMAIN: 05_REPORTING
TASK: implement_portfolio_metrics
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
Create a script that generates state/portfolio_showcase.json containing:
1. Total versions shipped (count git tags or version history)
2. Total missions ratified (count RATIFIED in MISSION_QUEUE)
3. Total strategies generated (count Zoo proposals)
4. Predatory Gate stats (survivors/killed/tested)
5. Factory accuracy (first-attempt pass rate)
6. Governance stats (constitutional violations: 0, breaches caught: 1)
7. Architecture summary (domains, tiers, models)
8. Timeline (first commit to current, versions per day)

This data feeds the README badges and any portfolio website.

## DELIVERABLE
File: scripts/export_portfolio_metrics.py

## CONSTRAINTS
- Read-only access to all state files
- Output valid JSON
- No external API calls
- Output valid Python only
"""

for fname, content, meta in [
    ("mission_domains_qwen35_update.md", m1, {
        "id": "domains_qwen35_update", "domain": "03_ORCHESTRATION",
        "task": "update_domains_model_roster", "type": "IMPLEMENTATION",
        "max_retries": 3, "priority": 1, "status": "PENDING",
        "authored_by": "Claude.ai — Supreme Council", "authored_at": now,
    }),
    ("mission_program_md.md", m2, {
        "id": "aos_program_md", "domain": "03_ORCHESTRATION",
        "task": "implement_program_md", "type": "ARCHITECTURE",
        "max_retries": 2, "priority": 2, "status": "PENDING",
        "authored_by": "Claude.ai — Supreme Council", "authored_at": now,
    }),
    ("mission_portfolio_metrics.md", m3, {
        "id": "portfolio_metrics_exporter", "domain": "05_REPORTING",
        "task": "implement_portfolio_metrics", "type": "IMPLEMENTATION",
        "max_retries": 3, "priority": 3, "status": "PENDING",
        "authored_by": "Claude.ai — Supreme Council", "authored_at": now,
    }),
]:
    (MISSIONS / fname).write_text(content)
    meta["mission_file"] = fname
    missions_data.append(meta)
    print(f"✅ {meta['id']}")

q = json.loads(QUEUE.read_text())
existing = {m["id"] for m in q["missions"]}
added = 0
for m in missions_data:
    if m["id"] not in existing:
        q["missions"].append(m)
        added += 1
QUEUE.write_text(json.dumps(q, indent=2))
print(f"\nLoaded {added} missions. Fire: python3 scripts/orchestrator_loop.py")
