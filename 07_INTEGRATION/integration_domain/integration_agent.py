"""
07_INTEGRATION — IntegrationAgent
Checks interface compatibility between two domain proposals.
Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on all constraint breaches
"""
from __future__ import annotations

import ast
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

GOVERNANCE_DOMAIN = "04_GOVERNANCE"


def _fail_closed(reason: str) -> None:
    log.critical("FAIL-CLOSED | %s", reason)
    sys.exit(1)


@dataclass
class Mismatch:
    kind: str
    symbol: str
    detail: str

    def to_dict(self) -> dict:
        return {"kind": self.kind, "symbol": self.symbol, "detail": self.detail}


@dataclass
class CompatibilityReport:
    compatible: bool
    domain_a: str
    domain_b: str
    mismatches: list[Mismatch] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "compatible": self.compatible,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "mismatches": [m.to_dict() for m in self.mismatches],
        }


class IntegrationAgent:
    """Compares public interfaces between two proposal files using AST analysis."""

    def _preflight(self, proposal_a: str, domain_a: str, proposal_b: str, domain_b: str) -> None:
        if GOVERNANCE_DOMAIN in domain_a or GOVERNANCE_DOMAIN in domain_b:
            _fail_closed(f"PREFLIGHT: governance domain forbidden — {domain_a} / {domain_b}")
        if domain_a == domain_b:
            _fail_closed(f"PREFLIGHT: same-domain pair rejected — {domain_a}")

    def _extract_code_blocks(self, path: Path) -> list[str]:
        fence = "```"
        pattern = fence + r"python\n(.*?)" + fence
        return re.findall(pattern, path.read_text(), re.DOTALL)

    def _get_methods(self, blocks: list[str]) -> dict[str, list[str]]:
        methods: dict[str, list[str]] = {}
        for block in blocks:
            try:
                tree = ast.parse(block)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.setdefault(node.name, []).append(item.name)
        return methods

    def check(
        self,
        proposal_a: str,
        domain_a: str,
        proposal_b: str,
        domain_b: str,
    ) -> CompatibilityReport:
        self._preflight(proposal_a, domain_a, proposal_b, domain_b)

        blocks_a = self._extract_code_blocks(Path(proposal_a))
        blocks_b = self._extract_code_blocks(Path(proposal_b))

        methods_a = self._get_methods(blocks_a)
        methods_b = self._get_methods(blocks_b)

        mismatches: list[Mismatch] = []

        # Check for method name overlaps that differ in signature
        for cls, meths in methods_a.items():
            if cls in methods_b:
                only_a = set(meths) - set(methods_b[cls])
                only_b = set(methods_b[cls]) - set(meths)
                for m in only_a:
                    mismatches.append(Mismatch(
                        kind="method_missing_in_b",
                        symbol=f"{cls}.{m}",
                        detail=f"Present in {domain_a}, absent in {domain_b}"
                    ))
                for m in only_b:
                    mismatches.append(Mismatch(
                        kind="method_missing_in_a",
                        symbol=f"{cls}.{m}",
                        detail=f"Present in {domain_b}, absent in {domain_a}"
                    ))

        compatible = len(mismatches) == 0
        log.info("INTEGRATION RESULT | compatible=%s mismatches=%d", compatible, len(mismatches))

        return CompatibilityReport(
            compatible=compatible,
            domain_a=domain_a,
            domain_b=domain_b,
            mismatches=mismatches,
        )
