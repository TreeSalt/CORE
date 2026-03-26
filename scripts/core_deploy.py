#!/usr/bin/env python3
"""core deploy — Extract code from ratified proposals and deploy to deliverable paths.
Usage: python3 scripts/core_deploy.py PROPOSAL.md [--dry-run]
"""
import re
import sys
import py_compile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def extract_deliverable_path(proposal_text: str) -> str | None:
    """Parse File: line in any format the factory produces."""
    patterns = [
        r'^\s*File:\s*[`"\']*([^\s`"\']+\.py)',      # File: path.py
        r'^\s*#\s*File:\s*([^\s]+\.py)',               # # File: path.py
        r'\*\*File:\s*[`"\']*([^\s`"\']+\.py)',        # **File: `path.py`**
    ]
    for line in proposal_text.split("\n"):
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
    return None


def extract_code_blocks(proposal_text: str) -> list[str]:
    """Extract all Python code blocks from markdown."""
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', proposal_text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def find_best_code_block(blocks: list[str]) -> str | None:
    """Select the largest code block that compiles cleanly."""
    valid = []
    for block in blocks:
        try:
            compile(block, "<proposal>", "exec")
            valid.append(block)
        except SyntaxError:
            continue
    if not valid:
        return None
    return max(valid, key=len)


def deploy(proposal_path: str, dry_run: bool = False) -> dict:
    """Extract code from a proposal and write to deliverable path."""
    proposal = Path(proposal_path)
    if not proposal.exists():
        return {"status": "ERROR", "reason": f"Proposal not found: {proposal_path}"}

    text = proposal.read_text()
    deliverable = extract_deliverable_path(text)
    blocks = extract_code_blocks(text)
    code = find_best_code_block(blocks)

    if not code:
        return {"status": "ERROR", "reason": "No valid Python code blocks found"}

    if not deliverable:
        print(f"No File: path found in proposal.")
        deliverable = input("Enter deliverable path (e.g., scripts/my_module.py): ").strip()
        if not deliverable:
            return {"status": "ERROR", "reason": "No deliverable path provided"}

    target = REPO_ROOT / deliverable
    
    # Syntax check
    try:
        compile(code, str(target), "exec")
    except SyntaxError as e:
        return {"status": "ERROR", "reason": f"Syntax error in extracted code: {e}"}

    result = {
        "status": "OK",
        "deliverable_path": str(deliverable),
        "code_length": len(code),
        "lines": code.count("\n") + 1,
        "proposal": str(proposal.name),
    }

    if dry_run:
        result["status"] = "DRY_RUN"
        print(f"DRY RUN — would write {result['lines']} lines to {deliverable}")
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code + "\n")
    print(f"DEPLOYED: {result['lines']} lines -> {deliverable}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/core_deploy.py PROPOSAL.md [--dry-run]")
        sys.exit(1)
    
    dry = "--dry-run" in sys.argv
    path = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    result = deploy(path, dry_run=dry)
    print(result)
