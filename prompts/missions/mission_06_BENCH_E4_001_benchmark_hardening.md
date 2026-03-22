# MISSION: Benchmark Runner Hardening
DOMAIN: 06_BENCHMARKING
TASK: harden_benchmark_runner
TYPE: IMPLEMENTATION

## CONTEXT
The benchmark runner needs hardening based on known false-positive patterns. Current issues: the hygiene check flags any code using sys.exit() without "fail_closed" present, but this should only trigger on explicit disable/skip patterns. Also add: timeout enforcement per benchmark (30s max), memory limit checking, and a summary report at the end of each run.

## DELIVERABLE
File: 06_BENCHMARKING/benchmark_hardening.py (patch module imported by benchmark_runner.py)

## REQUIREMENTS
- Fix the sys.exit() false positive pattern to only flag disable/skip patterns
- Add per-benchmark timeout (30s default, configurable)
- Add memory usage check (warn if benchmark uses >500MB)
- Generate a summary JSON report after each benchmark run
- No external API calls
- Output valid Python only
