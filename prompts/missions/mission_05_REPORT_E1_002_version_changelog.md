# Mission: Auto-Changelog Generator — Git Log to Markdown

## Domain
05_REPORTING

## Model Tier
Flash (4b)

## Description
Build a script that converts git log output into a clean Markdown changelog
grouped by version/drop number.

OUTPUT: scripts/changelog_generator.py
ALLOWED IMPORTS: json, typing, pathlib, datetime, subprocess, re
TEST: Parse 5 synthetic git log entries. Assert output has version headers. Assert commit messages preserved.

## Acceptance Criteria
- parse_git_log(repo_path, count=50) returns list of Commit objects
- group_by_version(commits) returns dict of version → commits
- generate_changelog(grouped) returns Markdown string
- Handles commits without version tags gracefully
