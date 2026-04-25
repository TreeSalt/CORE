# MISSION: test_coverage_analyzer
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E16_002_test_coverage_analyzer

## CONTEXT
E13.P24 escalated. This mission counts which mantis_core modules have
corresponding test files and reports coverage gaps.

## DELIVERABLE
File: scripts/test_coverage_analyzer.py

## INTERFACE CONTRACT
- Function: find_source_modules(source_root: Path) -> list[Path]
- Function: find_test_files(tests_root: Path) -> list[Path]
- Function: match_tests_to_sources(sources, tests) -> dict[Path, list[Path]]
- Function: report_coverage(matches: dict) -> CoverageReport
- Dataclass: CoverageReport (frozen)

## OUTPUT
JSON report listing covered, uncovered, and orphaned (test exists but
source doesn't) modules.
