#!/usr/bin/env python3
"""
auto_deploy.py — v3.1 (BRIEF-FIRST + UNFENCED CODE)
=====================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection

v3.1 PATCH: extract_code_blocks now handles proposals where the model
generates bare Python after the YAML frontmatter WITHOUT markdown code
fences. This was the root cause of the 0-deploy issue — models produce
correct code but without ``` fences, and the regex-only extractor
couldn't see it.

PRINCIPLE
'Algorithms for the deterministic, LLMs for the creative.'
The BRIEF tells us WHERE to deploy (sovereign-authored, deterministic).
The PROPOSAL tells us WHAT to deploy (model-authored, creative).
Never ask the model for the WHERE.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSALS_DIR = REPO_ROOT / "08_IMPLEMENTATION_NOTES"
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"
MISSION_QUEUE = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"

KNOWN_BUG_HASHES: set[str] = {
    "7e20f927b7f041073b9de0824ec53e1f8fdb22e8c10682e776a7a62a3895718a",
}

log = logging.getLogger("auto_deploy")

DELIVERABLE_PATTERNS = [
    re.compile(r'^\s*File:\s*[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'^\s*\*\*File:\*\*\s*[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'(?i)^\s*Deliverable:\s*[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'^###?\s*Deliverable[:\s]+[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'^\s*#\s*File:\s*([^\s]+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'^\s*-\s*File:\s*[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
    re.compile(r'^\s*-\s*\*\*File:\*\*\s*[`"\']*([^\s`"\']+\.(?:py|md|yaml|yml|json|html|txt))'),
]

# Tokens that indicate model prompt leak / generation boundary
PROMPT_LEAK_TOKENS = [
    "<|endoftext|>", "<|im_start|>", "<|im_end|>",
    "<|user|>", "<|assistant|>", "<|system|>", "<think>", "</think>",
]


def extract_code_blocks(proposal_path: Path) -> list[str]:
    """Return Python code blocks from proposal — fenced or unfenced.

    Models sometimes generate code inside ```python fences and sometimes
    generate bare code directly after the YAML frontmatter. This function
    handles both. Fenced blocks take priority when present.

    For unfenced code, everything after the closing --- of the YAML
    frontmatter is treated as a single code block, with any trailing
    model prompt tokens stripped.
    """
    text = proposal_path.read_text()

    # Strategy 1: fenced code blocks (```python ... ```)
    fenced = re.findall(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
    fenced = [b.strip() for b in fenced if b.strip()]
    if fenced:
        return fenced

    # Strategy 2: bare code after YAML frontmatter (--- ... ---)
    parts = text.split("---")
    if len(parts) >= 3:
        # parts[0] is before first ---, parts[1] is YAML, parts[2:] is code
        bare_code = "---".join(parts[2:]).strip()
    else:
        # No recognizable frontmatter — treat whole text as potential code
        bare_code = text.strip()

    # Strip trailing model prompt tokens
    for token in PROMPT_LEAK_TOKENS:
        if token in bare_code:
            bare_code = bare_code[:bare_code.index(token)].strip()

    # Only return if there's meaningful content
    if bare_code and len(bare_code) > 50:
        return [bare_code]

    return []


def find_best_block(blocks: list[str]) -> Optional[str]:
    """Return the longest code block that compiles without SyntaxError."""
    valid = []
    for block in blocks:
        try:
            compile(block, "<proposal>", "exec")
            valid.append(block)
        except SyntaxError:
            continue
    return max(valid, key=len) if valid else None


def extract_mission_id_from_proposal(proposal_path: Path) -> Optional[str]:
    """Parse proposal frontmatter for MISSION_ID field."""
    try:
        text = proposal_path.read_text()
    except Exception:
        return None
    for line in text.split("\n")[:30]:
        stripped = line.strip()
        match = re.match(
            r'^\**\s*MISSION[_ ]ID[:\s]+\s*`?([^\s`"\']+)`?',
            stripped, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
    return None


def _find_path_in_text(text: str) -> Optional[str]:
    """Scan text line by line for a deliverable path declaration."""
    in_deliverable_section = False
    for line in text.split("\n"):
        stripped = line.strip()

        if re.match(r'^#{1,3}\s*DELIVERABLE\s*$', stripped, re.IGNORECASE):
            in_deliverable_section = True
            continue

        if in_deliverable_section and stripped.startswith("#") and "DELIVERABLE" not in stripped.upper():
            in_deliverable_section = False

        for pattern in DELIVERABLE_PATTERNS:
            match = pattern.search(line)
            if match and match.lastindex and match.lastindex >= 1:
                candidate = match.group(1)
                if candidate.startswith("test_") and not in_deliverable_section:
                    continue
                return candidate

        if in_deliverable_section:
            bare_match = re.search(
                r'`([a-zA-Z_][a-zA-Z0-9_/]+\.(?:py|md|yaml|yml|json|html|txt))`',
                line
            )
            if bare_match:
                return bare_match.group(1)

    return None


def find_deliverable_path(
    proposal_path: Path,
    mission_file: Optional[str] = None
) -> Optional[str]:
    """Find deliverable path — BRIEF FIRST, proposal second."""
    if mission_file:
        mission_path = MISSIONS_DIR / mission_file
        if mission_path.exists():
            try:
                result = _find_path_in_text(mission_path.read_text())
                if result:
                    return result
            except Exception:
                pass

    try:
        result = _find_path_in_text(proposal_path.read_text())
        if result:
            return result
    except Exception:
        pass

    return None


def sha256_of_code(code: str) -> str:
    return hashlib.sha256((code + "\n").encode()).hexdigest()


def deploy_proposal(proposal_path: Path, mission: dict) -> dict:
    """Deploy code from proposal to the brief's deliverable path."""
    result = {
        "status": "UNKNOWN", "path": "", "lines": 0, "reason": "",
        "mission_id_match": None, "before_hash": None, "after_hash": None,
        "source_proposal_hash": None, "proposal": proposal_path.name,
        "mission_id": mission.get("id", ""),
    }

    try:
        proposal_bytes = proposal_path.read_bytes()
        result["source_proposal_hash"] = hashlib.sha256(proposal_bytes).hexdigest()
    except Exception as e:
        result["status"] = "ERROR_PROPOSAL_READ"
        result["reason"] = f"cannot read proposal: {e}"
        return result

    proposal_mission_id = extract_mission_id_from_proposal(proposal_path)
    target_mission_id = mission.get("id", "")
    if proposal_mission_id is not None:
        if proposal_mission_id != target_mission_id:
            result["status"] = "REFUSED_MISSION_ID_MISMATCH"
            result["reason"] = f"proposal MISSION_ID={proposal_mission_id} != {target_mission_id}"
            result["mission_id_match"] = False
            return result
        result["mission_id_match"] = True
    else:
        result["mission_id_match"] = None

    blocks = extract_code_blocks(proposal_path)
    code = find_best_block(blocks)
    if not code:
        result["status"] = "SKIPPED_NO_CODE"
        result["reason"] = f"no valid code blocks (fenced or unfenced) in {proposal_path.name}"
        return result

    code_hash = sha256_of_code(code)
    result["after_hash"] = code_hash
    result["lines"] = code.count("\n") + 1

    if code_hash in KNOWN_BUG_HASHES:
        result["status"] = "REFUSED_KNOWN_BUG"
        result["reason"] = f"code matches known bug hash {code_hash[:16]}"
        return result

    mission_file = mission.get("mission_file", "")
    deliverable = find_deliverable_path(proposal_path, mission_file)
    if not deliverable:
        result["status"] = "SKIPPED_NO_DELIVERABLE"
        result["reason"] = f"no deliverable path found in brief ({mission_file}) or proposal"
        return result

    result["path"] = deliverable
    target = REPO_ROOT / deliverable

    if target.exists():
        try:
            existing_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            result["before_hash"] = existing_hash
            if existing_hash == code_hash:
                result["status"] = "SKIPPED_ALREADY_CORRECT"
                result["reason"] = "target exists with matching content"
                return result
            else:
                result["status"] = "SKIPPED_ALREADY_DIFFERENT"
                result["reason"] = f"target exists, different content (existing={existing_hash[:16]})"
                return result
        except Exception as e:
            result["status"] = "ERROR_TARGET_READ"
            result["reason"] = f"cannot read existing target: {e}"
            return result

    try:
        compile(code, str(target), "exec")
    except SyntaxError as e:
        result["status"] = "ERROR_SYNTAX"
        result["reason"] = f"syntax error: {e}"
        return result

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code + "\n")
    except Exception as e:
        result["status"] = "ERROR_WRITE"
        result["reason"] = f"write failed: {e}"
        return result

    try:
        post_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    except Exception as e:
        result["status"] = "ERROR_POST_READ"
        result["reason"] = f"cannot verify: {e}"
        return result

    if post_hash != code_hash:
        result["status"] = "ERROR_POST_WRITE_HASH_MISMATCH"
        result["reason"] = "post-write hash mismatch"
        return result

    result["status"] = "DEPLOYED"
    log.info(f"DEPLOYED {deliverable} ({result['lines']} lines) from {proposal_path.name}")
    return result


def deploy_all_ratified(queue_path: Optional[Path] = None) -> list[dict]:
    """Deploy code for all RATIFIED missions."""
    if queue_path is None:
        queue_path = MISSION_QUEUE
    try:
        queue = json.loads(queue_path.read_text())
    except Exception as e:
        log.error(f"cannot read queue: {e}")
        return []

    results: list[dict] = []

    for mission in queue.get("missions", []):
        if mission.get("status") != "RATIFIED":
            continue

        mission_id = mission.get("id", "")
        domain = mission.get("domain", "")
        if not domain:
            continue

        domain_proposals = sorted(
            PROPOSALS_DIR.glob(f"PROPOSAL_{domain}_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        matched_proposal: Optional[Path] = None
        for prop in domain_proposals:
            if extract_mission_id_from_proposal(prop) == mission_id:
                matched_proposal = prop
                break

        if matched_proposal is None:
            if not domain_proposals:
                continue
            matched_proposal = domain_proposals[0]
            log.warning(
                f"LEGACY MATCH: no proposal with MISSION_ID={mission_id}, "
                f"falling back to latest in {domain}: {matched_proposal.name}"
            )

        result = deploy_proposal(matched_proposal, mission)
        results.append(result)

    deployed = sum(1 for r in results if r["status"] == "DEPLOYED")
    skipped = sum(1 for r in results if r["status"].startswith("SKIPPED"))
    refused = sum(1 for r in results if r["status"].startswith("REFUSED"))
    errors = sum(1 for r in results if r["status"].startswith("ERROR"))

    print(f"AUTO-DEPLOY COMPLETE: {deployed} deployed, {skipped} skipped, {refused} refused, {errors} errors")
    for r in results:
        if r["status"] == "DEPLOYED":
            print(f"  DEPLOYED: {r['path']} ({r['lines']} lines) from {r['proposal']}")
        elif r["status"] == "SKIPPED_NO_DELIVERABLE":
            print(f"  NO_PATH: {r['mission_id']} — {r['reason']}")
        elif r["status"] == "SKIPPED_NO_CODE":
            print(f"  NO_CODE: {r['mission_id']} — {r['reason']}")
        elif r["status"].startswith("REFUSED"):
            print(f"  REFUSED: {r['mission_id']} — {r['reason']}")
        elif r["status"].startswith("ERROR"):
            print(f"  ERROR:   {r['mission_id']} — {r['reason']}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    deploy_all_ratified()
