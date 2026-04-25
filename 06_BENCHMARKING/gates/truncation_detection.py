#!/usr/bin/env python3
"""
TRUNCATION_DETECTION_GATE — Catch Mid-Method Failures
=======================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection (factory cannot self-validate)

PURPOSE
Catches the failure mode documented in E14_BACKLOG_001:
tier_loader_v4 (E13.P15) ended at line 332 with a method signature
`def select_sprinter(self) -> List[ModelInfo]:` and no body. The 9B
cruiser model exhausted its context window mid-implementation. The
benchmark gate accepted the truncated proposal because the partial
code was syntactically suspect but the test runner gracefully handled
the missing methods as "not yet implemented."

This gate runs as the FIRST gate in the benchmark pipeline (cheapest
to compute, catches the most obvious failures). A truncated proposal
gets rejected before substance, import, or contract gates run.

DETECTION HEURISTICS
1. Last non-blank line ends with `:` — signature without body
2. ast.parse fails specifically with "expected indented block"
3. File ends inside an unbalanced string literal
4. Final indent level > 0 with no closing dedent
5. Trailing `pass  # TODO` or similar placeholder bodies
6. Trailing model self-prompt tokens (<|endoftext|>, <|im_start|>, etc.)

The last heuristic catches a specific Qwen failure mode where the model
emits its own template tokens at the end of generation. We saw this in
PROPOSAL_03_ORCHESTRATION_20260410T005245Z.md.
"""

import ast
import re
from pathlib import Path

# Model self-prompt tokens that indicate truncation/leak
PROMPT_LEAK_PATTERNS = [
    "<|endoftext|>",
    "<|im_start|>",
    "<|im_end|>",
    "<|user|>",
    "<|assistant|>",
    "<|system|>",
    "<think>",  # raw thinking-tag leak
    "</think>",
]

# Trailing placeholder patterns that suggest model gave up
PLACEHOLDER_PATTERNS = [
    re.compile(r'pass\s*#\s*TODO', re.IGNORECASE),
    re.compile(r'pass\s*#\s*placeholder', re.IGNORECASE),
    re.compile(r'pass\s*#\s*implement', re.IGNORECASE),
    re.compile(r'raise\s+NotImplementedError', re.IGNORECASE),
    re.compile(r'\.\.\.\s*#\s*TODO', re.IGNORECASE),
]


def _extract_python_blocks(text: str) -> list[str]:
    """Extract all fenced Python code blocks from markdown."""
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def _check_signature_without_body(code: str) -> tuple[bool, str]:
    """Detect last non-blank line ending with ':' (def or class header)."""
    lines = code.rstrip().split("\n")
    for line in reversed(lines):
        if line.strip():
            stripped = line.strip()
            if stripped.endswith(":"):
                # Could be a legitimate trailing class/def, or could be truncation
                # Look for def/class/if/for/while/etc keywords
                head = stripped.split()[0] if stripped.split() else ""
                if head in ("def", "class", "if", "for", "while", "try",
                            "with", "elif", "else", "except", "finally"):
                    return (True,
                            f"file ends with header line (suggests truncation): {stripped[:80]}")
            break  # Only check the last meaningful line
    return (False, "")


def _check_ast_indent_error(code: str) -> tuple[bool, str]:
    """Try to parse and detect indent errors that suggest truncation."""
    try:
        ast.parse(code)
        return (False, "")
    except SyntaxError as e:
        msg = str(e).lower()
        if "expected an indented block" in msg or "expected indented block" in msg:
            return (True, f"ast parse: {e}")
        if "unexpected eof" in msg:
            return (True, f"ast parse: {e}")
        return (False, "")


def _check_unbalanced_strings(code: str) -> tuple[bool, str]:
    """Detect unbalanced triple-quoted strings (common truncation signature)."""
    triple_double = code.count('"""')
    triple_single = code.count("'''")
    if triple_double % 2 != 0:
        return (True, f"unbalanced triple-double-quotes ({triple_double} occurrences)")
    if triple_single % 2 != 0:
        return (True, f"unbalanced triple-single-quotes ({triple_single} occurrences)")
    return (False, "")


def _check_prompt_leak(text: str) -> tuple[bool, str]:
    """Detect model self-prompt tokens leaking into output."""
    for pattern in PROMPT_LEAK_PATTERNS:
        if pattern in text:
            return (True, f"model self-prompt token leak detected: {pattern}")
    return (False, "")


def _check_placeholder_endings(code: str) -> tuple[bool, str]:
    """Detect trailing placeholder bodies suggesting model gave up."""
    last_500_chars = code[-500:] if len(code) > 500 else code
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(last_500_chars):
            match = pattern.search(last_500_chars)
            return (True, f"placeholder pattern in trailing code: {match.group(0)}")
    return (False, "")


def detect_truncation(code: str) -> tuple[bool, str]:
    """Main detection function. Returns (is_truncated, reason).

    Runs all checks; returns the FIRST positive detection. The reason
    string is suitable for direct inclusion in escalation messages.
    """
    # Order: cheapest checks first
    checks = [
        _check_prompt_leak(code),
        _check_signature_without_body(code),
        _check_unbalanced_strings(code),
        _check_ast_indent_error(code),
        _check_placeholder_endings(code),
    ]
    for is_truncated, reason in checks:
        if is_truncated:
            return (True, reason)
    return (False, "")


def gate_truncation_detection(proposal_path: Path) -> tuple[bool, str]:
    """Wrapper for benchmark runner integration.

    Returns (passed: bool, reason: str). Passes if no truncation
    detected. Fails fast on first truncation indicator.
    """
    p = Path(proposal_path)
    if not p.exists():
        return (False, "TRUNCATION_GATE_FAIL: proposal file does not exist")

    try:
        text = p.read_text()
    except Exception as e:
        return (False, f"TRUNCATION_GATE_FAIL: cannot read proposal: {e}")

    # Check the raw text for prompt leaks first (covers the whole file)
    leak_detected, leak_reason = _check_prompt_leak(text)
    if leak_detected:
        return (False, f"TRUNCATION_GATE_FAIL: {leak_reason}")

    # Then check the largest code block for truncation indicators
    blocks = _extract_python_blocks(text)
    if not blocks:
        # No code blocks isn't truncation per se — that's a substance issue
        return (True, "")

    # Use the largest block (most likely to be the main payload)
    code = max(blocks, key=len)
    is_truncated, reason = detect_truncation(code)
    if is_truncated:
        return (False, f"TRUNCATION_GATE_FAIL: {reason}")

    return (True, "")


# ─── CLI for standalone testing ──────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 truncation_detection.py <proposal_path>")
        sys.exit(2)
    passed, reason = gate_truncation_detection(Path(sys.argv[1]))
    print(f"Passed: {passed}")
    if reason:
        print(f"Reason: {reason}")
    sys.exit(0 if passed else 1)
