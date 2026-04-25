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
    """
    Atomically writes the dashboard JSON state file.
    
    Args:
        pipeline_state: The dictionary containing the current pipeline state.
        output_path: The filesystem path where the JSON state file should be written.
    """
    directory = os.path.dirname(output_path) or '.'

    if not os.path.exists(directory):
        os.makedirs(directory)

    fd, temp_path = tempfile.mkstemp(dir=directory, suffix='.tmp')
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(pipeline_state, f)
            # Ensure data is flushed to OS buffer
            f.flush()
            # Ensure data is written to physical disk
            os.fsync(f.fileno())
        
        # Atomic rename operation (POSIX and Windows compatible if same filesystem)
        os.replace(temp_path, output_path)
        
    except Exception:
        # Clean up temporary file on failure before re-raising
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise