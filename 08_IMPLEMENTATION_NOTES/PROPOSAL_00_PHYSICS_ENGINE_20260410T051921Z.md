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
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)

class PaperTradeValidator:
    def validate_run(self, actual_fills, expected_fills) -> ValidationReport:
        errors = []
        
        # Normalize inputs to lists
        if not isinstance(actual_fills, list):
            actual_fills = [actual_fills] if actual_fills else []
        if not isinstance(expected_fills, list):
            expected_fills = [expected_fills] if expected_fills else []

        # Validate count
        actual_count = len(actual_fills)
        expected_count = len(expected_fills)
        
        if actual_count != expected_count:
            errors.append(f"Fill count mismatch: Expected {expected_count}, Got {actual_count}")

        # Compare fills by index (assuming ordered comparison for paper trade validation)
        min_len = min(actual_count, expected_count)
        for i in range(min_len):
            actual_fill = actual_fills[i]
            expected_fill = expected_fills[i]
            
            if not isinstance(actual_fill, dict):
                actual_fill = {}
            if not isinstance(expected_fill, dict):
                expected_fill = {}

            # Check Symbol
            if actual_fill.get('symbol') != expected_fill.get('symbol'):
                errors.append(f"Fill {i}: Symbol mismatch. Expected '{expected_fill.get('symbol')}', Got '{actual_fill.get('symbol')}'")
            
            # Check Quantity
            if actual_fill.get('quantity') != expected_fill.get('quantity'):
                errors.append(f"Fill {i}: Quantity mismatch. Expected {expected_fill.get('quantity')}, Got {actual_fill.get('quantity')}")
            
            # Check Price
            if actual_fill.get('price') != expected_fill.get('price'):
                errors.append(f"Fill {i}: Price mismatch. Expected {expected_fill.get('price')}, Got {actual_fill.get('price')}")

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            metrics={
                'actual_count': actual_count,
                'expected_count': expected_count,
                'error_count': len(errors)
            }
        )