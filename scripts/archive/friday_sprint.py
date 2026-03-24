#!/usr/bin/env python3
"""
SPRINT: Friday Night → Sunday 2pm — Phase 1C + Epoch 3 Prep
=============================================================
AUTHOR: Claude (Hostile Auditor)
DATE: 2026-03-13

STRATEGY: The factory just proved it can eat 12 missions in 2h18m.
We have ~44 hours until Sunday 2pm. That's time for 3-4 full batches
if needed. This sprint focuses on:

  1. PREDATORY GATE EXECUTION — run all 10 strategies through stress test
  2. EPOCH 3 PREP — Alpha Synthesis mission (Graveyard + Champion data)
  3. RED TEAM ENGINE FOUNDATION — adversarial prompt generation
  4. COUNCIL_CANON DEDUP FIX — the pubkey append bug
"""
import json
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(".")
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"
QUEUE_FILE = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
now = datetime.now(timezone.utc).isoformat()
missions = []

# ══════════════════════════════════════════════════════════════════════════════
# 1. PREDATORY GATE EXECUTION — stress test the Zoo
# ══════════════════════════════════════════════════════════════════════════════

gate_runner_content = """# MISSION: Predatory Gate Runner — Execute Stress Tests
DOMAIN: 06_BENCHMARKING
TASK: implement_predatory_gate_runner
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The Predatory Gate module exists (ratified). Now we need a runner script
that executes it against all Zoo strategies and produces the results.

## BLUEPRINT
Create a script that:
1. Discovers all Zoo strategy proposals in 08_IMPLEMENTATION_NOTES/
2. Extracts the Python class from each proposal
3. Instantiates each strategy
4. Runs it through the Predatory Gate's 4 scenarios (COVID, Flash Crash, Fed Pivot, Gap Down)
5. Writes PREDATORY_GATE_REPORT.json with per-strategy, per-scenario results
6. Strategies that breach 15% max drawdown → writes GRAVEYARD.md entry
7. Survivors listed in state/predatory_gate_survivors.json

## DELIVERABLE
File: scripts/run_predatory_gate.py

## CONSTRAINTS
- Must be runnable as: python3 scripts/run_predatory_gate.py
- Read drawdown threshold from CHECKPOINTS.yaml
- Write results to state/ directory
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_predatory_gate_runner.md").write_text(gate_runner_content)
missions.append({
    "id": "predatory_gate_runner",
    "domain": "06_BENCHMARKING",
    "task": "implement_predatory_gate_runner",
    "mission_file": "mission_predatory_gate_runner.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 1,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Phase 1C: execute Predatory Gate against all 10 Zoo strategies",
})
print("✅ 1: Predatory Gate Runner")

# ══════════════════════════════════════════════════════════════════════════════
# 2. EPOCH 3 — Alpha Synthesis Mission Generator
# ══════════════════════════════════════════════════════════════════════════════

synth_content = """# MISSION: Alpha Synthesis Mission Generator
DOMAIN: 03_ORCHESTRATION
TASK: implement_alpha_synthesis_generator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, Epoch 3 uses LLM-guided gene-splicing. The 32B Heavy Lifter
reads the Champion Registry (winners) alongside the Graveyard (anti-patterns)
and synthesizes hybrid strategies combining winning traits.

## BLUEPRINT
Create a module that:
1. Reads state/champion_registry.json (or state/predatory_gate_survivors.json)
2. Reads docs/GRAVEYARD.md for anti-patterns
3. For each pair of surviving strategies, generates a MISSION file that:
   - Names the hybrid (e.g., "E3_001_gatekeeper_x_squeeze")
   - Describes which traits to combine from parent A and parent B
   - Explicitly lists anti-patterns from Graveyard as "DO NOT" constraints
   - Includes the correct prepare_data() interface spec
4. Writes missions to prompts/missions/ and adds them to MISSION_QUEUE.json
5. Maximum 5 hybrids per epoch (hardware budget constraint)

## DELIVERABLE
File: scripts/alpha_synthesis.py

## CONSTRAINTS
- Read-only access to Graveyard and Champion Registry
- Mission files go to prompts/missions/ (standard path)
- Queue entries follow existing schema exactly
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_alpha_synthesis.md").write_text(synth_content)
missions.append({
    "id": "alpha_synthesis_generator",
    "domain": "03_ORCHESTRATION",
    "task": "implement_alpha_synthesis_generator",
    "mission_file": "mission_alpha_synthesis.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 2,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "ROADMAP v3.0: Epoch 3 Alpha Synthesis preparation",
})
print("✅ 2: Alpha Synthesis Generator")

# ══════════════════════════════════════════════════════════════════════════════
# 3. RED TEAM ENGINE — Adversarial Prompt Generator
# ══════════════════════════════════════════════════════════════════════════════

redteam_content = """# MISSION: Red Team Engine — Adversarial Prompt Generator
DOMAIN: 08_CYBERSECURITY
TASK: implement_adversarial_prompt_generator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Red Team Engine productizes our governance lessons.
This first module generates adversarial mission prompts designed to test
whether the benchmark runner and governance gates catch known attack patterns.

## BLUEPRINT
Create a module that generates test mission files containing:
1. HALLUCINATION PROBES: missions that encourage importing non-existent libraries
2. GOVERNANCE BYPASS: missions with forged "Authored_By: Sovereign" signatures
3. DOMAIN BOUNDARY: missions that instruct agents to write to 04_GOVERNANCE/
4. CREDENTIAL LEAKS: missions containing API key patterns in the task description
5. PRE-RATIFICATION: missions with "Status: RATIFIED" already set
6. QUEUE FLOODING: batch of 100+ identical missions to test rate limiting

For each probe type, generate:
- The adversarial mission file
- The expected benchmark result (should FAIL with specific gate + reason)
- A test assertion that validates the benchmark caught it

Output: a test suite that validates our governance gates catch all known attacks.

## DELIVERABLE
File: 08_CYBERSECURITY/cybersecurity/adversarial_prompt_generator.py
Test: 06_BENCHMARKING/tests/08_CYBERSECURITY/test_adversarial_prompts.py

## CONSTRAINTS
- Generated probes must be OBVIOUSLY adversarial (no subtle attacks)
- Must not actually execute the adversarial missions — only generate them
- Test suite validates that benchmark_runner rejects them
- No external API calls
- Output valid Python only
"""
(MISSIONS_DIR / "mission_adversarial_prompts.md").write_text(redteam_content)
missions.append({
    "id": "adversarial_prompt_generator",
    "domain": "08_CYBERSECURITY",
    "task": "implement_adversarial_prompt_generator",
    "mission_file": "mission_adversarial_prompts.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 3,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "ROADMAP v3.0 Phase 3C: Red Team Engine foundation",
})
print("✅ 3: Adversarial Prompt Generator (Red Team Engine)")

# ══════════════════════════════════════════════════════════════════════════════
# 4. INTENT COMPILER — Phase 2 Foundation
# ══════════════════════════════════════════════════════════════════════════════

intent_content = """# MISSION: Intent Compiler — Natural Language to Mission
DOMAIN: 03_ORCHESTRATION
TASK: implement_intent_compiler
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Intent Compiler bridges imprecise human input to
fully-specified factory missions. This is an ARCHITECTURE proposal — design
the interface and data flow, not the full implementation (that requires
cloud LLM access for natural language understanding).

## BLUEPRINT
Design the Intent Compiler architecture:
1. Input interface: accepts natural language string + operator context
2. Context gathering: reads DOMAINS.yaml, CHECKPOINTS.yaml, Champion Registry,
   Graveyard, Hardware state, OPERATOR_INSTANCE.yaml
3. Output: a fully-specified MISSION_QUEUE entry with all required fields
4. Validation: runs Prompt Quality Validator on generated mission before queue
5. Escalation: if confidence < threshold, asks human for clarification

Document the data flow as a class skeleton with method signatures,
docstrings, and type hints. Include example input/output pairs.

## DELIVERABLE
File: 03_ORCHESTRATION/orchestration_domain/intent_compiler.py

## CONSTRAINTS
- ARCHITECTURE proposal — class skeleton + docstrings, not full implementation
- Must reference all existing governance files by path
- Must include the Prompt Quality Validator as a pre-queue gate
- No external API calls in the skeleton
- Output valid Python only
"""
(MISSIONS_DIR / "mission_intent_compiler.md").write_text(intent_content)
missions.append({
    "id": "intent_compiler_architecture",
    "domain": "03_ORCHESTRATION",
    "task": "implement_intent_compiler",
    "mission_file": "mission_intent_compiler.md",
    "type": "ARCHITECTURE",
    "max_retries": 2,
    "priority": 4,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "ROADMAP v3.0 Phase 2B: generalization layer architecture",
})
print("✅ 4: Intent Compiler Architecture")

# ══════════════════════════════════════════════════════════════════════════════
# 5. COUNCIL_CANON FIX
# ══════════════════════════════════════════════════════════════════════════════

canon_fix_content = """# MISSION: Fix COUNCIL_CANON.yaml Duplicate Pubkey Bug
DOMAIN: 03_ORCHESTRATION
TASK: fix_council_canon_dedup
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The forge's _sync_council_canon() function in antigravity_harness/forge/build.py
appends sovereign_pubkey_sha256 on every build instead of replacing the existing
line. This causes the YAML file to accumulate duplicate entries.

## BLUEPRINT
Fix the _sync_council_canon() function:
1. Find the re.sub() call that writes sovereign_pubkey_sha256
2. Change it from appending to replacing — if the key already exists, update it
3. After the fix, the YAML should have exactly ONE sovereign_pubkey_sha256 line
4. Add a post-write validation: read back the file, count occurrences, assert == 1

## DELIVERABLE
A patch description for antigravity_harness/forge/build.py

## CONSTRAINTS
- ONLY modify the _sync_council_canon() function
- Do NOT change any other function in build.py
- The fix must be idempotent (running forge multiple times produces same result)
- Output valid Python only
"""
(MISSIONS_DIR / "mission_canon_dedup_fix.md").write_text(canon_fix_content)
missions.append({
    "id": "council_canon_dedup_fix",
    "domain": "03_ORCHESTRATION",
    "task": "fix_council_canon_dedup",
    "mission_file": "mission_canon_dedup_fix.md",
    "type": "IMPLEMENTATION",
    "max_retries": 3,
    "priority": 5,
    "status": "PENDING",
    "authored_by": "Claude.ai — Supreme Council",
    "authored_at": now,
    "rationale": "Cosmetic but persistent bug — 14+ duplicate lines per build",
})
print("✅ 5: COUNCIL_CANON Dedup Fix")

# ══════════════════════════════════════════════════════════════════════════════
# UPDATE QUEUE
# ══════════════════════════════════════════════════════════════════════════════

queue = json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else {"missions": []}
existing_ids = {m["id"] for m in queue["missions"]}
added = 0
for m in missions:
    if m["id"] not in existing_ids:
        queue["missions"].append(m)
        added += 1
QUEUE_FILE.write_text(json.dumps(queue, indent=2))

print(f"""
{'='*60}
FRIDAY → SUNDAY SPRINT LOADED
{'='*60}

MISSIONS: {len(missions)} new ({added} added to queue)

1. Predatory Gate Runner     — stress test all 10 Zoo strategies
2. Alpha Synthesis Generator — Epoch 3 hybrid strategy creation tool
3. Adversarial Prompt Gen    — Red Team Engine foundation
4. Intent Compiler           — ARCHITECTURE for generalization layer
5. COUNCIL_CANON Fix         — persistent dedup bug

ESTIMATED TIME: ~1-2 hours (5 missions, most first-attempt)

AFTER FACTORY COMPLETES:
  If Predatory Gate Runner passes → run it:
    python3 scripts/run_predatory_gate.py
  This produces the survivor list for Alpha Synthesis.

  If Alpha Synthesis passes → run it:
    python3 scripts/alpha_synthesis.py
  This generates Epoch 3 mission files and queues them.

  Then re-run the orchestrator for Epoch 3:
    python3 scripts/orchestrator_loop.py

EXECUTION:
  git add -A && git commit -m "feat: Friday sprint — predatory gate + alpha synthesis + red team engine"
  make drop
  python3 scripts/orchestrator_loop.py
""")
