# MISSION: Benchmark Summary Report Generator
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/benchmark_report.py

## REQUIREMENTS
- Read all benchmark results from 06_BENCHMARKING/reports/
- Aggregate: total benchmarks run, pass rate, common failure reasons
- Identify flaky benchmarks (pass sometimes, fail sometimes)
- Output Markdown: reports/benchmarks/BENCH_SUMMARY_{timestamp}.md
- Output JSON alongside for dashboard consumption
- No external API calls
- Output valid Python only
