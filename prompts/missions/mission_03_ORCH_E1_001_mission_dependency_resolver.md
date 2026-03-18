# Mission: Mission Dependency Resolver — Topological Sort

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Build a dependency resolver that topologically sorts missions based on
their depends_on fields, ensuring prerequisites complete before dependents.

REQUIREMENTS:
- Parse mission queue JSON with depends_on fields
- Build directed acyclic graph (DAG) of dependencies
- Detect cycles and raise clear error
- Return execution order as topologically sorted list
- Group independent missions into parallel batches

OUTPUT: scripts/dependency_resolver.py
ALLOWED IMPORTS: json, typing, pathlib, dataclasses, collections
TEST: Create 8 missions with diamond dependency (A→B, A→C, B→D, C→D). Assert D is last. Assert A is first. Create cycle (A→B→A). Assert CycleError raised.

## Acceptance Criteria
- load_missions(path) returns list of Mission objects
- build_dag(missions) returns adjacency dict
- detect_cycles(dag) returns list of cycle paths or empty list
- topological_sort(dag) returns ordered list of mission IDs
- batch_independent(sorted_missions, dag) returns list of parallel batches
- Raises CycleError with descriptive message on circular dependency
