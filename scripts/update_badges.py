#!/usr/bin/env python3
"""Update README.md badges from actual repo state. Run: python3 scripts/update_badges.py

Idempotent: produces zero file changes if state is unchanged. Safe to run
under pre-commit hooks without triggering "files modified" failures.

Source of truth:
- Version: mantis_core/__init__.py __version__
- Missions ratified: orchestration/MISSION_QUEUE.json (status == "RATIFIED")
- Pass rate: ratified / total from same queue
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"


def get_version():
    """Read version from mantis_core/__init__.py"""
    init = REPO / "mantis_core" / "__init__.py"
    if init.exists():
        for line in init.read_text().splitlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.0.0"


def get_mission_stats():
    """Read mission queue. Returns (ratified_count, total_count)."""
    queue = REPO / "orchestration" / "MISSION_QUEUE.json"
    if not queue.exists():
        return 0, 0
    data = json.loads(queue.read_text())
    missions = data.get("missions", [])
    ratified = sum(1 for m in missions if m.get("status") == "RATIFIED")
    total = len(missions)
    return ratified, total


def get_pass_rate():
    """Calculate pass rate from current queue."""
    ratified, total = get_mission_stats()
    if total == 0:
        return 0
    return int(ratified / total * 100)


def compute_new_readme(current_text: str) -> str:
    """Pure function: given current README text, return updated text.
    Does not touch filesystem. Used by both update_readme and verification.
    """
    version = get_version()
    ratified, _total = get_mission_stats()
    pass_rate = get_pass_rate()

    text = current_text
    text = re.sub(
        r'version-[0-9]+\.[0-9]+\.[0-9]+-blue',
        f'version-{version}-blue',
        text,
    )
    text = re.sub(
        r'missions_ratified-[0-9]+\+?-green',
        f'missions_ratified-{ratified}+-green',
        text,
    )
    text = re.sub(
        r'factory_pass_rate-[0-9]+%25-brightgreen',
        f'factory_pass_rate-{pass_rate}%25-brightgreen',
        text,
    )
    return text


def update_readme():
    """Idempotent README update. Returns True if file was modified, False if no-op."""
    current = README.read_text()
    new = compute_new_readme(current)

    version = get_version()
    ratified, total = get_mission_stats()
    pass_rate = get_pass_rate()

    if new == current:
        print("Badges unchanged (no write needed):")
        print(f"  Version:    {version}")
        print(f"  Missions:   {ratified}/{total} RATIFIED")
        print(f"  Pass rate:  {pass_rate}%")
        return False

    README.write_text(new)
    print("Badges updated:")
    print(f"  Version:    {version}")
    print(f"  Missions:   {ratified}/{total} RATIFIED")
    print(f"  Pass rate:  {pass_rate}%")
    return True


if __name__ == "__main__":
    update_readme()
    sys.exit(0)
