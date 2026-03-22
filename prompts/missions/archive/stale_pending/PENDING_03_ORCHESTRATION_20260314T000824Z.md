# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Compute Scheduler — VRAM Resource Manager
DOMAIN: 03_ORCHESTRATION
TASK: implement_compute_scheduler
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI STRATEGIC SUGGESTION
As the Champion Registry grows, the orchestrator needs a strict local
resource scheduler to prevent the 32b Heavy Lifter from colliding with
the paper trading data streams. The GTX 1070 has 8GB VRAM and 32GB
system RAM — both are shared resources.

## BLUEPRINT
Create a ComputeScheduler class that:
1. Reads orchestration/VRAM_STATE.json for current GPU utilization
2. Maintains a priority queue of compute requests:
   - P0: Paper trading (real-time, cannot be interrupted)
   - P1: Predatory Gate runs (time-sensitive)
   - P2: Factory missions (can wait)
   - P3: Background tasks (lowest priority)
3. Before dispatching a mission to Ollama:
   - Check VRAM availability (8GB total, model needs vary)
   - If 32b model needed but paper trading is running → queue
   - If 7b model suffices → dispatch immediately (fits alongside)
4. Writes scheduling decisions to state/compute_schedule.json
5. Provides should_dispatch(model_size, priority) -> bool

## DELIVERABLE
File: 03_ORCHESTRATION/orchestration_domain/compute_scheduler.py

## CONSTRAINTS
- Never interrupt P0 (paper trading) for P2 (factory) work
- Must be queryable by orchestrator_loop.py before dispatch
- Log all scheduling decisions
- No external API calls
- Output valid Python only
TASK: implement_compute_scheduler
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.