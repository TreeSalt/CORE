#!/usr/bin/env python3
"""auto_deploy.py — Automatically extract and deploy code from ratified proposals.

Called after every successful ratification. Extracts Python code from the
proposal markdown, finds the deliverable path from the mission file,
and writes the code to disk.

This eliminates the deployment gap permanently. The factory generates,
the benchmark validates, the sovereign ratifies, and auto_deploy ships.

Design principle: The sovereign should NEVER manually extract code from proposals.
"""
import re
import json
import logging
import py_compile
from pathlib import Path

log = logging.getLogger("auto_deploy")
REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSALS_DIR = REPO_ROOT / "08_IMPLEMENTATION_NOTES"
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"


def extract_code_blocks(proposal_path: Path) -> list[str]:
    """Extract all Python code blocks from a proposal markdown."""
    text = proposal_path.read_text()
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def find_best_block(blocks: list[str]) -> str | None:
    """Return the longest code block that compiles without SyntaxError."""
    valid = []
    for block in blocks:
        try:
            compile(block, "<proposal>", "exec")
            valid.append(block)
        except SyntaxError:
            continue
    return max(valid, key=len) if valid else None


def find_deliverable_path(proposal_path: Path, mission_file: str = None) -> str | None:
    """Find deliverable path from proposal or corresponding mission file.
    
    Checks proposal first (File: line in any format), then falls back
    to the mission file if provided.
    """
    text = proposal_path.read_text()
    
    # Check proposal for File: patterns
    patterns = [
        r'^\s*File:\s*[`"\']*([^\s`"\']+\.py)',
        r'^\s*#\s*File:\s*([^\s]+\.py)',
        r'\*\*File:\s*[`"\']*([^\s`"\']+\.py)',
    ]
    for line in text.split("\n"):
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
    
    # Fall back to mission file
    if mission_file:
        mission_path = MISSIONS_DIR / mission_file
        if mission_path.exists():
            mission_text = mission_path.read_text()
            for line in mission_text.split("\n"):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
    
    return None


def deploy_proposal(proposal_path: Path, mission_file: str = None) -> dict:
    """Extract code from proposal and deploy to deliverable path.
    
    Returns: {"status": "DEPLOYED"|"SKIPPED"|"ERROR", "path": str, "lines": int, "reason": str}
    """
    blocks = extract_code_blocks(proposal_path)
    code = find_best_block(blocks)
    
    if not code:
        return {"status": "SKIPPED", "path": "", "lines": 0,
                "reason": "No valid Python code blocks in proposal"}
    
    deliverable = find_deliverable_path(proposal_path, mission_file)
    if not deliverable:
        return {"status": "SKIPPED", "path": "", "lines": len(code.split("\n")),
                "reason": "No deliverable path found in proposal or mission"}
    
    target = REPO_ROOT / deliverable
    
    # Don't overwrite existing files unless the proposal is newer
    if target.exists():
        return {"status": "SKIPPED", "path": str(deliverable), "lines": 0,
                "reason": f"File already exists: {deliverable}"}
    
    # Syntax check before writing
    try:
        compile(code, str(target), "exec")
    except SyntaxError as e:
        return {"status": "ERROR", "path": str(deliverable), "lines": 0,
                "reason": f"Syntax error: {e}"}
    
    # Deploy
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code + "\n")
    
    lines = code.count("\n") + 1
    log.info(f"AUTO-DEPLOY: {deliverable} ({lines} lines)")
    return {"status": "DEPLOYED", "path": str(deliverable), "lines": lines, "reason": ""}


def deploy_all_ratified(queue_path: Path = None) -> list[dict]:
    """Deploy code from all ratified proposals that haven't been deployed yet.
    
    Reads the mission queue to find ratified missions, locates their proposals,
    and deploys any that have code and a deliverable path.
    """
    if queue_path is None:
        queue_path = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
    
    queue = json.loads(queue_path.read_text())
    results = []
    
    for mission in queue.get("missions", []):
        if mission.get("status") != "RATIFIED":
            continue
        
        domain = mission.get("domain", "")
        mission_file = mission.get("mission_file", "")
        
        # Find the latest proposal for this domain
        proposals = sorted(
            PROPOSALS_DIR.glob(f"PROPOSAL_{domain}_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not proposals:
            continue
        
        # Try deploying the most recent proposal
        result = deploy_proposal(proposals[0], mission_file)
        result["mission_id"] = mission.get("id", "")
        result["proposal"] = proposals[0].name
        results.append(result)
        
        if result["status"] == "DEPLOYED":
            log.info(f"  {mission.get('id')}: DEPLOYED -> {result['path']}")
        elif result["status"] == "SKIPPED":
            pass  # Normal — file exists or no deliverable path
        else:
            log.warning(f"  {mission.get('id')}: {result['status']} — {result['reason']}")
    
    deployed = [r for r in results if r["status"] == "DEPLOYED"]
    skipped = [r for r in results if r["status"] == "SKIPPED"]
    errors = [r for r in results if r["status"] == "ERROR"]
    
    print(f"AUTO-DEPLOY COMPLETE: {len(deployed)} deployed, {len(skipped)} skipped, {len(errors)} errors")
    for r in deployed:
        print(f"  DEPLOYED: {r['path']} ({r['lines']} lines) from {r['proposal']}")
    for r in errors:
        print(f"  ERROR: {r['mission_id']} — {r['reason']}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    deploy_all_ratified()
