---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from pathlib import Path


def dedup_canon():
    filepath = Path("docs/ready_to_drop/COUNCIL_CANON.yaml")
    with open(filepath, 'r') as f:
        original_lines = f.readlines()

    seen = set()
    unique_lines = []
    for line in original_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    removed_count = len(original_lines) - len(unique_lines)

    with open(filepath, 'w') as f:
        f.writelines(unique_lines)

    print(f"{removed_count} duplicate lines were removed")


if __name__ == "__main__":
    dedup_canon()