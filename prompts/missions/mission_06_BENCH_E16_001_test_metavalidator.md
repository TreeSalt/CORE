# MISSION: test_metavalidator
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E16_001_test_metavalidator

## CONTEXT
E13.P16 was PENDING — never ran. This mission validates that test files
actually exercise the contracts they claim to test. Helps catch the
"empty test that passes vacuously" anti-pattern.

## DELIVERABLE
File: scripts/test_metavalidator.py

## INTERFACE CONTRACT
- Function: find_test_files(tests_root: Path) -> list[Path]
- Function: extract_imported_modules(test_file: Path) -> list[str]
- Function: extract_called_functions(test_file: Path) -> list[str]
- Function: validate_test_substance(test_file: Path) -> ValidationReport
- Dataclass: ValidationReport (frozen) with fields: file, asserts_count, calls_to_target, vacuous

A test is "vacuous" if it has assert count = 0 OR if no calls reference
the module it claims to test.
