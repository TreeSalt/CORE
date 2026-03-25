#!/usr/bin/env python3
"""Update README.md badges from actual repo state. Run: python3 scripts/update_badges.py"""
import json
import re
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
    """Count ratified missions from queue history"""
    queue = REPO / "orchestration" / "MISSION_QUEUE.json"
    if not queue.exists():
        return 0, 0
    data = json.loads(queue.read_text())
    missions = data.get("missions", [])
    ratified = sum(1 for m in missions if m.get("status") == "RATIFIED")
    total = len(missions)
    return ratified, total


def get_total_ratified():
    """Count all ratified proposals across all epochs"""
    notes = REPO / "08_IMPLEMENTATION_NOTES"
    if not notes.exists():
        return 0
    return len(list(notes.glob("PROPOSAL_*.md")))


def get_pass_rate():
    """Calculate pass rate from current queue"""
    ratified, total = get_mission_stats()
    if total == 0:
        return 0
    return int(ratified / total * 100)


def update_readme():
    text = README.read_text()
    version = get_version()
    total_proposals = get_total_ratified()
    pass_rate = get_pass_rate()

    # Update version badge
    text = re.sub(r'version-[0-9]+\.[0-9]+\.[0-9]+-blue', f'version-{version}-blue', text)

    # Update missions badge (use total proposals as proxy for cumulative ratified)
    text = re.sub(r'missions_ratified-[0-9]+\+-green', f'missions_ratified-{total_proposals}+-green', text)

    # Update pass rate badge
    text = re.sub(r'factory_pass_rate-[0-9]+%25-brightgreen', f'factory_pass_rate-{pass_rate}%25-brightgreen', text)

    README.write_text(text)
    print(f"Badges updated:")
    print(f"  Version:    {version}")
    print(f"  Proposals:  {total_proposals}+")
    print(f"  Pass rate:  {pass_rate}%")


if __name__ == "__main__":
    update_readme()
