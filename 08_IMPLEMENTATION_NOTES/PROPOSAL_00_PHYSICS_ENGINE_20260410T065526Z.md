---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import json
import os
import tempfile


def write_dashboard_state(pipeline_state, output_path) -> None:
    """Atomically writes the dashboard JSON state file."""
    target_dir = os.path.dirname(os.path.abspath(output_path))
    if not target_dir:
        target_dir = '.'

    fd, temp_path = tempfile.mkstemp(dir=target_dir, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(pipeline_state, f)
        os.rename(temp_path, output_path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise