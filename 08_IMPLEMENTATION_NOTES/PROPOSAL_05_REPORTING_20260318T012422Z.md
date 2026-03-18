---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

 ```python
from typing import List, Dict, NamedTuple
import json
import typing
import pathlib
import datetime
import subprocess
import re

class Commit(NamedTuple):
    version: str
    commit_message: str
    timestamp: datetime.datetime

def parse_git_log(repo_path: str, count: int = 50) -> List[Commit]:
    git_log_output = subprocess.check_output(['git', '-C', repo_path, 'log', '--pretty=format:%B%n%h%n%ai', '-n', str(count)])
    commits = []
    lines = git_log_output.decode('utf-8').split('\n')
    i = 0
    while i < len(lines):
        commit_message = lines[i].strip()
        commit_hash = lines[i + 1]
        timestamp = datetime.datetime.fromisoformat(lines[i + 2])
        version_match = re.match(r'^v(\d+\.\d+\.\d+)$', commit_message)
        version = version_match.group(1) if version_match else 'unversioned'
        commits.append(Commit(version, commit_message, timestamp))
        i += 3
    return commits

def group_by_version(commits: List[Commit]) -> Dict[str, List[Commit]]:
    grouped = {}
    for commit in commits:
        if commit.version not in grouped:
            grouped[commit.version] = []
        grouped[commit.version].append(commit)
    return grouped

def generate_changelog(grouped: Dict[str, List[Commit]]) -> str:
    changelog = []
    for version, commits in grouped.items():
        changelog.append(f'## {version}\n')
        for commit in commits:
            changelog.append(f'- {commit.commit_message} ({commit.timestamp.strftime("%Y-%m-%d")})\n')
    return '\n'.join(changelog)

# Example usage
if __name__ == "__main__":
    repo_path = '/path/to/your/repo'
    commits = parse_git_log(repo_path)
    grouped = group_by_version(commits)
    changelog = generate_changelog(grouped)
    print(changelog)
```

This script provides a basic implementation of the required functionality. It defines a `Commit` named tuple to store commit information, and implements functions to parse the git log, group commits by version, and generate a Markdown changelog. The example usage at the bottom demonstrates how to use these functions.