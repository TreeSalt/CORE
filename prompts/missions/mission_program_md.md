# MISSION: Create AOS program.md — Karpathy-Style Agent Instructions
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
