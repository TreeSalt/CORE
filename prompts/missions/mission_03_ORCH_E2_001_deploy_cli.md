# Mission: 03_ORCH_E2_001_deploy_cli

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Integrate the core deploy command into the CORE CLI (scripts/core_cli.py).

REQUIREMENTS:
1. Add 'core deploy' command that calls scripts/deploy_proposals.py
2. Add 'core deploy --list' to show ratified but undeployed proposals
3. Add 'core deploy --dry-run' to preview what would be extracted
4. Register in COMMANDS dict and argument parser
5. Add to help menu under MISSIONS section

The deploy_proposals.py script already exists from the factory.
This mission ONLY adds the CLI wrapper.

ALLOWED IMPORTS: subprocess, sys, pathlib (already imported in core_cli.py)
OUTPUT: Updated scripts/core_cli.py with cmd_deploy function
TEST: Assert 'core deploy --help' does not error.
