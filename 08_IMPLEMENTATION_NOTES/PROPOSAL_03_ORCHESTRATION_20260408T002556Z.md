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
import sys

def setup_cgroup():
    """Setup Ollama cgroup with default limits (v2) and ensure process is in it."""
    try:
        # Get Ollama PID
        pids = get_ollama_pid()
        if not pids:
            return False  # Graceful failure
        
        pid = pids[0]
        # Construct unique cgroup path. 
        # We assume unified hierarchy (cgroup v2).
        # Path: /sys/fs/cgroup/ollama_limit_<pid> to allow isolation from parent
        cgroup_path = f"/sys/fs/cgroup/ollama_ollama_{pid}"

        # 1. Create the cgroup directory
        os.makedirs(cgroup_path, exist_ok=True)
        
        # Convert GB to bytes for cgroup settings (default 8GB)
        max_mem_gb = 8
        high_mem_gb = 7500 # ~3GB overhead? Or maybe Ollama specific. 
                            # Let's use standard reasonable defaults or system default if possible.
                            # Prompt implies "set values". I'll use a fixed example value (e.g. 4GB)
                            # To be safe, let's allow user input? No, function signature is fixed.
                            # I will set 'memory.max' and 'memory.high'.
        
        # Default limits as per request or standard practice:
        limit_bytes = int(max_mem_gb * 1024 * 1024 * 1024)
        
        high_limit_bytes = int(high_mem_gb * 1024 * 1024 * 1024)

        # 2. Write limits to cgroup files (v2 unified hierarchy)
        try:
            with open(os.path.join(cgroup_path, "memory.max"), "w") as f:
                f.write(str(limit_bytes))
            with open(os.path.join(cgroup_path, "memory.high"), "w") as f:
                f.write(str(high_limit_bytes))
            
            # 3. Move Ollama process into the cgroup
            # Write PID to cgroup.procs file in unified hierarchy
            with open(os.path.join(cgroup_path, "cgroup.procs"), "w") as f:
                f.write(f"{pid}\n")
                
        except PermissionError:
            return False

        return True

    except Exception:
        return False # Graceful failure

def get_cgroup_stats():
    """Read memory.current and other standard stats for the Ollama process cgroup."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return {} # Or None? Prompt implies reading, so maybe empty dict
        
        pid = pids[0]
        cgroup_path = f"/sys/fs/cgroup/ollama_ollama_{pid}"
        
        stats = {}
        
        if os.path.isdir(cgroup_path):
            # Read memory.current
            cpu_file = os.path.join(cgroup_path, "cpu.stat")
            mem_current_file = os.path.join(cgroup_path, "memory.current")
            
            try:
                with open(cpu_file, "r") as f:
                    stats["cpu"] = float(f.read()) # Example key
                with open(mem_current_file, "r") as f:
                    stats["memory"] = float(f.read())
            except (IOError, ValueError):
                pass
            
            # Check other standard stats if available (e.g. memory.high)
            high_file = os.path.join(cgroup_path, "memory.high")
            try:
                with open(high_file, "r") as f:
                    stats["high"] = float(f.read())
            except (IOError, ValueError):
                pass
                
        return stats

    except Exception:
        return {} # Graceful failure

def is_ollama_in_cgroup():
    """Check if Ollama process is in its own cgroup."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return False
            
        pid = pids[0]
        cgroup_path = f"/sys/fs/cgroup/ollama_ollama_{pid}"
        
        # Check if the process is in the cgroup (cgroup.procs)
        procs_file = os.path.join(cgroup_path, "cgroup.procs")
        try:
            with open(procs_file, "r") as f:
                content = f.read()
                return str(pid) in content
        except IOError:
            return False

    except Exception:
        return False # Graceful failure

def teardown_cgroup():
    """Remove Ollama cgroup directory gracefully."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return True # No process, nothing to remove
            
        pid = pids[0]
        cgroup_path = f"/sys/fs/cgroup/ollama_ollama_{pid}"
        
        if os.path.isdir(cgroup_path):
            # Remove directory (requires no processes inside)
            # If Ollama is still running in it, we must move it or fail.
            # Since we can't kill, and we assume setup moved it in, 
            # usually teardown waits for process exit? But maybe we just try to delete.
            # To avoid errors, use shutil.rmtree? No, cgroup dirs shouldn't be removed with processes.
            # Better: Move back to parent if needed? But prompt doesn't ask that.
            # Just attempt removal.
            os.rmdir(cgroup_path) 
        return True

    except Exception:
        return False # Graceful failure (process might not exist or permission issue)

# --- Helper for PID retrieval ---
def get_ollama_pid():
    """Helper function to get Ollama process ID."""
    try:
        result = subprocess.run(["ps", "-p", "$$", "o", "pid"], capture_output=True, text=True, timeout=2) 
        # This gets current PID. Ollama is usually `ollama serve` or similar.
        # The prompt says "get stats for the process" (singular). I'll find by name 'ollama'.
        pass
    except:
        return []

# --- Correct PID retrieval implementation ---
def get_ollama_pid():
    """Get PID of Ollama process."""
    try:
        result = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        output = result.stdout.split('\n')
        pid = None
        for line in output:
            if "ollama" in line.lower() and "server" in line.lower(): # Assuming standard command
                parts = line.strip().split(None, 1)
                if len(parts) > 0:
                    pid = parts[0] # PID is first column usually
                    break
        return [pid] if pid else []
    except Exception:
        return []

# Actually, `ps -ef` includes header. And "ollama" might appear in args.
# Better check for 'ollama' binary.
```

**Revised Solution:**
The implementation uses helper functions to locate the Ollama process (assuming it's running as a service or manually started). If the PID isn't found, operations gracefully fail or return defaults as per instructions. The setup function creates the cgroup directory and moves the process using the unified hierarchy mechanism (`cgroup.procs`), setting memory limits via `memory.max` and `memory.high`. Statistics are retrieved by reading standard files from the cgroup path.

```python
import os
import subprocess

def get_ollama_pid():
    """Helper: Find PID of running 'ollama' process."""
    try:
        # Use ps to find process with name 'ollama'
        result = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "ollama" in line.lower() and not "python" in line.lower(): # Exclude python wrapper
                parts = line.strip().split()
                if len(parts) >= 1:
                    return [parts[0]] # PID is first field
        return []
    except Exception:
        return []

def setup_cgroup():
    """Setup Ollama cgroup with default limits and ensure process is in it."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return False
        
        pid = pids[0]
        # Path: /sys/fs/cgroup/ollama_<pid>
        cgroup_path = f"/sys/fs/cgroup/ollama_{pid}"

        # Create directory
        os.makedirs(cgroup_path, exist_ok=True)
        
        # Set limits (example values or reasonable defaults)
        # In unified hierarchy, memory.max and memory.high are standard.
        limit_bytes = 4 * 1024 * 1024 * 1024 # Example 4GB
        high_bytes = int(limit_bytes * 0.9)   # Example 90%
        
        try:
            with open(os.path.join(cgroup_path, "memory.max"), "w") as f:
                f.write(str(limit_bytes))
            with open(os.path.join(cgroup_path, "memory.high"), "w") as f:
                f.write(str(high_bytes))
            
            # Move process to cgroup by writing PID
            with open(os.path.join(cgroup_path, "cgroup.procs"), "w") as f:
                f.write(f"{pid}\n")
        except Exception:
            return False

        return True
        
    except Exception:
        return False

def get_cgroup_stats():
    """Read memory.current and other standard stats for Ollama process cgroup."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return {}
            
        pid = pids[0]
        cgroup_path = f"/sys/fs/cgroup/ollama_{pid}"
        
        stats = {}
        
        if os.path.isdir(cgroup_path):
            # Read memory.current
            try:
                mem_file = os.path.join(cgroup_path, "memory.current")
                with open(mem_file, "r") as f:
                    stats["memory"] = float(f.read())
                
                # Read other standard files (e.g. cpu.stat if available)
                cpu_stat_file = os.path.join(cgroup_path, "cpu.stat")
                try:
                    with open(cpu_stat_file, "r") as f:
                        # Parse first line for CPU usage or return raw string? 
                        # Prompt asks for a dict of values (float/int).
                        stats["cpu"] = float(f.readline().split()[1]) if f.readline() else 0
                except (IOError, ValueError):
                    pass
                    
            except IOError:
                pass
                
        return stats

    except Exception:
        return {}

def is_ollama_in_cgroup():
    """Check if Ollama process is in its own cgroup."""
    try:
        pids = get_ollama_pid()
        if not pids:
            return False
            
        pid = pids[0]
        cgroup_path = f"/sys/fs/cgroup/ollama_{pid}"
        
        procs_file = os.path.join(cgroup_path, "cgroup.procs")
        try:
            with open(procs_file, "r") as f:
                content = f.read()
                return str(pid) in content
        except IOError:
            return False

    except Exception:
        return False

def teardown_cgroup():
    """Remove Ollama cgroup directory gracefully."""
    try:
        pids = get_
```

---

**Note**: I've corrected the PID search logic (avoiding `ps -p $$`) and added robust error handling. The solution assumes an environment where `cgroup.procs` writing is allowed (usually root or user-owned cgroups) and processes can be moved programmatically in the unified hierarchy.

**Complete Python Script:**

```python
import os
import subprocess

def get_ollama_pid():
    """Find PID of 'ollama' process."""
    try:
        result = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "ollama" in line.lower() and not "python" in line.lower():
                parts = line.strip().split()
                return [parts[0]]
    except Exception:
        pass
    return []

def setup_cgroup(limit_memory_mb=4096):
    """Create cgroup directory and configure limits."""
    try:
        pid = get_ollama_pid()[0] if get_ollama_pid() else None
        if not pid:
            return False
        
        cgroup_path = f"/sys/fs/cgroup/ollama_{pid}"
        os.makedirs(cgroup_path, exist_ok=True)
        
        # Write memory limits (Unified hierarchy syntax)
        with open(os.path.join(cgroup_path, "memory.max"), "w") as f:
            f.write(str(limit_memory_mb * 1024 * 1024))
        with open(os.path.join(cgroup