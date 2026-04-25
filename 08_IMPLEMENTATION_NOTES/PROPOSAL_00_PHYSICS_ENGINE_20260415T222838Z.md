---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ValidationReport:
    is_valid: bool
    message: str
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

class PaperTradeValidator:
    def validate_run(self, actual_fills: List[Dict[str, Any]], expected_fills: List[Dict[str, Any]]) -> ValidationReport:
        if not isinstance(actual_fills, list):
            return ValidationReport(
                is_valid=False,
                message="Invalid input type for actual_fills",
                summary={"actual_count": 0, "expected_count": len(expected_fills) if isinstance(expected_fills, list) else 0}
            )
        if not isinstance(expected_fills, list):
            return ValidationReport(
                is_valid=False,
                message="Invalid input type for expected_fills",
                summary={"actual_count": len(actual_fills), "expected_count": 0}
            )

        actual_count = len(actual_fills)
        expected_count = len(expected_fills)
        summary = {"actual_count": actual_count, "expected_count": expected_count}

        if actual_count != expected_count:
            return ValidationReport(
                is_valid=False,
                message=f"Fill count mismatch: {actual_count} vs {expected_count}",
                discrepancies=[{"error_type": "count_mismatch", "actual": actual_count, "expected": expected_count}],
                summary=summary
            )

        discrepancies = []
        
        try:
            sorted_actual = sorted(actual_fills, key=lambda x: x.get('order_id', str(x)))
            sorted_expected = sorted(expected_fills, key=lambda x: x.get('order_id', str(x)))
            
            for actual_fill, expected_fill in zip(sorted_actual, sorted_expected):
                if actual_fill != expected_fill:
                    discrepancies.append({
                        "error_type": "content_mismatch",
                        "actual": actual_fill,
                        "expected": expected_fill
                    })
            
            is_valid = len(discrepancies) == 0
            status_msg = "PASS" if is_valid else f"FAIL: {len(discrepancies)} discrepancies found"
            
        except Exception as e:
            return ValidationReport(
                is_valid=False,
                message=f"Comparison error: {str(e)}",
                summary=summary
            )

        return ValidationReport(
            is_valid=is_valid,
            message=status_msg,
            discrepancies=discrepancies,
            summary=summary
        )