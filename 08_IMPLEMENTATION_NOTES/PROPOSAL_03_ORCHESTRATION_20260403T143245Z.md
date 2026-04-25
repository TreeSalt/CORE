---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import subprocess
import os
import logging
from pathlib import Path


def setup_cgroup(memory_max_gb, memory_high_gb):
    """Setup Ollama cgroup slice with specified memory limits."""
    try:
        # Check if cgroups v2 is available
        if not os.path.exists("/sys/fs/cgroup"):
            logging.error("cgroups mount point not found")
            return False
        
        # Verify cgroups v2 controller exists
        cg_version = Path("/sys/fs/cgroup/cgroup.controllers").exists()
        if not cg_version:
            logging.error("cgroups v2 not available")
            return False
        
        # Run the bash script to setup cgroup
        bash_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_cgroup_setup.sh")
        
        if not os.path.exists(bash_script_path):
            logging.error(f"Bash script not found at {bash_script_path}")
            return False
        
        cmd = [
            "bash", bash_script_path,
            str(memory_max_gb),
            str(memory_high_gb)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        logging.info(f"Cgroup setup command output: {result.stdout}")
        
        return result.returncode == 0
        
    except PermissionError as e:
        logging.error(f"Permission denied: {e}")
        return False
    except Exception as e:
        logging.error(f"Failed to setup cgroup: {e}")
        return False


def get_cgroup_stats():
    """Read memory.current, memory.max from cgroup."""
    try:
        slice_path = Path("/sys/fs/cgroup/slices/ollama-managed.slice")
        
        if not slice_path.exists():
            logging.warning("ollama-managed.slice not found")
            return None
        
        stats = {}
        
        # Try to read from slice directory
        for mem_type in ["memory.current", "memory.max"]:
            mem_file = slice_path / mem_type
            try:
                value = mem_file.read_text().strip()
                if "." in str(value):
                    value = float(value)
                else:
                    value = int(value)
                stats[mem_type] = value
            except FileNotFoundError:
                logging.warning(f"File {mem_type} not found")
                continue
        
        return stats if stats else None
        
    except Exception as e:
        logging.error(f"Failed to get cgroup stats: {e}")
        return None


def is_ollama_in_cgroup():
    """Verify Ollama PID assignment to the slice."""
    try:
        # Get current Ollama process PIDs
        ollama_pids = []
        for pid in Path("/proc").iterdir():
            if pid.is_dir() and pid.name.isdigit():
                try:
                    with open(f"/proc/{pid}/cmdline", "r") as f:
                        cmdline = f.read()
                        if "ollama" in cmdline.lower():
                            ollama_pids.append(int(pid))
                except (IOError, OSError):
                    continue
        
        # Check cgroup slice for Ollama processes
        slice_path = Path("/sys/fs/cgroup/slices/ollama-managed.slice")
        
        if not slice_path.exists():
            return False
        
        try:
            with open(slice_path / "cgroup.procs", "r") as f:
                cgroup_pids = [int(line.strip()) for line in f.readlines() if line.strip()]
        except (IOError, OSError):
            logging.warning("Cannot read cgroup.procs file")
            return False
        
        # Check if any Ollama PIDs are in the slice
        matched_pids = set(ollama_pids) & set(cgroup_pids)
        logging.info(f"Ollama PIDs in cgroup: {matched_pids}")
        
        return len(matched_pids) > 0
        
    except Exception as e:
        logging.error(f"Failed to check Ollama cgroup assignment: {e}")
        return False


def teardown_cgroup():
    """Remove ollama-managed.slice."""
    try:
        slice_path = Path("/sys/fs/cgroup/slices/ollama-managed.slice")
        
        if not slice_path.exists():
            logging.info("ollama-managed.slice already removed or doesn't exist")
            return True
        
        # Need to stop processes in the slice first
        cgroup_procs_file = slice_path / "cgroup.procs"
        
        try:
            with open(cgroup_procs_file, "r") as f:
                pids_in_slice = [int(line.strip()) for line in f.readlines() if line.strip()]
            
            # Kill processes in the slice
            for pid in pids_in_slice:
                try:
                    os.kill(pid, 15)  # SIGTERM first
                except (OSError, ProcessLookupError):
                    pass
        except FileNotFoundError:
            logging.warning("Cannot read cgroup.procs to kill processes")
        
        # Remove the slice file
        try:
            slice_path.unlink()
            logging.info("Successfully removed ollama-managed.slice")
            return True
        except FileNotFoundError:
            logging.info("ollama-managed.slice not found after cleanup")
            return True
            
    except Exception as e:
        logging.error(f"Failed to teardown cgroup: {e}")
        return False
```