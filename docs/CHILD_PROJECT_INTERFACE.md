# CORE → Child Project Interface

CORE provides governance infrastructure consumed by MANTIS and SPECTER.

## What CORE Exports

### Orchestration
- `orchestration/semantic_router.py` — model routing, tier selection, VRAM gating
- `orchestration/dynamic_timeout.py` — hardware-adaptive timeout management
- `scripts/orchestrator_loop.py` — mission queue processing
- `scripts/run_loop.py` — generate → benchmark → ratify → deploy loop

### Benchmarking
- `06_BENCHMARKING/benchmark_runner.py` — hygiene gates, AST validation, import checks
- `06_BENCHMARKING/benchmark_schema.yaml` — constitutional violation patterns

### Governance
- `04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md` — founding document
- `04_GOVERNANCE/OPERATOR_INSTANCE.yaml` — operator configuration
- `04_GOVERNANCE/DOMAINS.yaml` — domain registry with tier/security config

### Red Team
- `scripts/red_team/` — probe generation, response analysis, campaign running

## What CORE Does NOT Export

- Trading strategies, signals, or execution logic (MANTIS)
- Bug bounty targets, recon profiles, or submission tracking (SPECTER)
- Any proprietary algorithm or data feed adapter
- API keys, credentials, or customer data

## Interface Contract

Child projects consume CORE via:
1. `pip install -e /path/to/CORE` (development)
2. `pip install core-governance` (when published to PyPI)
3. Git submodule (if preferred)

CORE's public API is the orchestration pipeline:
- Write mission briefs in `prompts/missions/`
- Run `core run --daemon` to process the queue
- Ratified proposals auto-deploy to the child project's write_path
