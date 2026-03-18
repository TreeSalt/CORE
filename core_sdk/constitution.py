"""core_sdk.constitution — Constitutional governance config loader."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import json
import re

def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat/nested key-value DOMAINS.yaml."""
    result = {}
    current_key = None
    current_dict = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            current_key = stripped[:-1].strip()
            current_dict = {}
            result[current_key] = current_dict
        elif indent > 0 and current_dict is not None:
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                current_dict[k.strip()] = v.strip().strip("\"'")
    return result

def load_domains(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return _parse_simple_yaml(text)
    return json.loads(text)

def validate_domain(domain_id: str, domains: dict) -> bool:
    if domain_id not in domains:
        return False
    d = domains[domain_id]
    return all(k in d for k in ("security", "model_tier"))

def get_security_classification(domain_id: str, domains: dict) -> str:
    return domains.get(domain_id, {}).get("security", "UNKNOWN")

def get_model_tier(domain_id: str, domains: dict) -> str:
    return domains.get(domain_id, {}).get("model_tier", "UNKNOWN")

def is_human_only(domain_id: str, domains: dict) -> bool:
    sec = get_security_classification(domain_id, domains)
    return sec.upper() == "HUMAN_ONLY"
